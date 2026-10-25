using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

namespace QfliLuaAudit {
    public sealed class ProcessResult {
        public int RootProcessId;
        public uint? RootExitCode;
        public bool TimedOut;
        public bool ResidualTreeTerminated;
        public bool TreeEmpty;
        public int[] ObservedProcessIds = new int[0];
        public string Error;
    }

    public static class BoundedProcess {
        [StructLayout(LayoutKind.Sequential)]
        struct SecurityAttributes { public int Length; public IntPtr Descriptor;
            [MarshalAs(UnmanagedType.Bool)] public bool Inherit; }
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        struct StartupInfo {
            public int Size; public string Reserved; public string Desktop; public string Title;
            public uint X, Y, XSize, YSize, XCountChars, YCountChars, FillAttribute, Flags;
            public ushort ShowWindow, ReservedSize; public IntPtr ReservedBytes;
            public IntPtr Input, Output, Error;
        }
        [StructLayout(LayoutKind.Sequential)]
        struct ProcessInfo { public IntPtr Process, Thread; public uint ProcessId, ThreadId; }
        [StructLayout(LayoutKind.Sequential)]
        struct BasicLimit {
            public long ProcessTime, JobTime; public uint Flags;
            public UIntPtr MinWorkingSet, MaxWorkingSet; public uint ActiveLimit;
            public UIntPtr Affinity; public uint Priority, Scheduling;
        }
        [StructLayout(LayoutKind.Sequential)]
        struct IoCounters { public ulong ReadOps, WriteOps, OtherOps, ReadBytes, WriteBytes, OtherBytes; }
        [StructLayout(LayoutKind.Sequential)]
        struct ExtendedLimit {
            public BasicLimit Basic; public IoCounters Io;
            public UIntPtr ProcessMemory, JobMemory, PeakProcessMemory, PeakJobMemory;
        }
        [StructLayout(LayoutKind.Sequential)]
        struct Accounting {
            public long User, Kernel, PeriodUser, PeriodKernel;
            public uint Faults, TotalProcesses, ActiveProcesses, TerminatedProcesses;
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        static extern IntPtr CreateJobObject(IntPtr attributes, string name);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool SetInformationJobObject(IntPtr job, int kind, ref ExtendedLimit info, int length);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool QueryInformationJobObject(IntPtr job, int kind, out Accounting info, int length, IntPtr returned);
        [DllImport("kernel32.dll", SetLastError = true, EntryPoint = "QueryInformationJobObject")]
        static extern bool QueryProcessIds(IntPtr job, int kind, IntPtr info, int length, IntPtr returned);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool TerminateJobObject(IntPtr job, uint exitCode);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        static extern bool CreateProcess(string application, StringBuilder command, IntPtr processAttributes,
            IntPtr threadAttributes, bool inheritHandles, uint flags, IntPtr environment,
            string directory, ref StartupInfo startup, out ProcessInfo process);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        static extern IntPtr CreateFile(string name, uint access, uint share,
            ref SecurityAttributes attributes, uint creation, uint flags, IntPtr template);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern uint ResumeThread(IntPtr thread);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool TerminateProcess(IntPtr process, uint exitCode);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool GetExitCodeProcess(IntPtr process, out uint exitCode);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool CloseHandle(IntPtr handle);

        static void Check(bool succeeded, string operation) {
            if (!succeeded) throw new Win32Exception(Marshal.GetLastWin32Error(), operation);
        }
        static string Quote(string value) {
            StringBuilder quoted = new StringBuilder("\""); int slashes = 0;
            foreach (char c in value) {
                if (c == '\\') { slashes++; continue; }
                if (c == '"') { quoted.Append('\\', slashes * 2 + 1); quoted.Append(c); }
                else { quoted.Append('\\', slashes); quoted.Append(c); }
                slashes = 0;
            }
            quoted.Append('\\', slashes * 2); quoted.Append('"'); return quoted.ToString();
        }
        static IntPtr OpenInherited(string name, uint access, uint creation) {
            SecurityAttributes attributes = new SecurityAttributes();
            attributes.Length = Marshal.SizeOf(typeof(SecurityAttributes)); attributes.Inherit = true;
            IntPtr handle = CreateFile(name, access, 3, ref attributes, creation, 0x80, IntPtr.Zero);
            if (handle == new IntPtr(-1)) throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateFile " + name);
            return handle;
        }
        static uint ActiveCount(IntPtr job) {
            Accounting info;
            Check(QueryInformationJobObject(job, 1, out info, Marshal.SizeOf(typeof(Accounting)), IntPtr.Zero), "Query job accounting");
            return info.ActiveProcesses;
        }
        static void Observe(IntPtr job, HashSet<int> ids) {
            int length = 8 + IntPtr.Size * 4096;
            IntPtr buffer = Marshal.AllocHGlobal(length);
            try {
                Check(QueryProcessIds(job, 3, buffer, length, IntPtr.Zero), "Query owned job PIDs");
                int count = Marshal.ReadInt32(buffer, 4);
                for (int i = 0; i < count; i++) ids.Add(Marshal.ReadIntPtr(buffer, 8 + IntPtr.Size * i).ToInt32());
            } finally { Marshal.FreeHGlobal(buffer); }
        }

        public static ProcessResult Run(string executable, string[] arguments, string directory,
            string stdout, string stderr, int maxMilliseconds, Action<int> onStarted) {
            ProcessResult result = new ProcessResult();
            HashSet<int> ids = new HashSet<int>(); object gate = new object();
            IntPtr job = IntPtr.Zero, output = IntPtr.Zero, error = IntPtr.Zero, input = IntPtr.Zero;
            ProcessInfo process = new ProcessInfo(); Timer deadline = null;
            bool assigned = false; Stopwatch elapsed = Stopwatch.StartNew();
            try {
                job = CreateJobObject(IntPtr.Zero, null);
                if (job == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(), "Create owned job");
                ExtendedLimit limit = new ExtendedLimit(); limit.Basic.Flags = 0x2000; // KILL_ON_JOB_CLOSE; no BREAKAWAY_OK
                Check(SetInformationJobObject(job, 9, ref limit, Marshal.SizeOf(typeof(ExtendedLimit))), "Set kill-on-close job");
                output = OpenInherited(stdout, 0x40000000, 2);
                error = OpenInherited(stderr, 0x40000000, 2);
                input = OpenInherited("NUL", 0x80000000, 3);
                StartupInfo startup = new StartupInfo(); startup.Size = Marshal.SizeOf(typeof(StartupInfo));
                startup.Flags = 0x100; startup.Input = input; startup.Output = output; startup.Error = error;
                StringBuilder command = new StringBuilder(Quote(executable));
                foreach (string argument in arguments) command.Append(" ").Append(Quote(argument));
                Check(CreateProcess(executable, command, IntPtr.Zero, IntPtr.Zero, true,
                    0x08000004, IntPtr.Zero, directory, ref startup, out process), "Create suspended owned process");
                result.RootProcessId = checked((int)process.ProcessId); ids.Add(result.RootProcessId);
                Check(AssignProcessToJobObject(job, process.Process), "Assign suspended process to job"); assigned = true;
                int remaining = maxMilliseconds - checked((int)elapsed.ElapsedMilliseconds);
                if (remaining <= 0) { result.TimedOut = true; throw new TimeoutException("Deadline expired before resume"); }
                deadline = new Timer(delegate(object unused) {
                    lock (gate) {
                        if (job != IntPtr.Zero) {
                            result.TimedOut = true;
                            if (!TerminateJobObject(job, 124)) result.Error = "Deadline termination failed: " + Marshal.GetLastWin32Error();
                        }
                    }
                }, null, remaining, Timeout.Infinite);
                if (onStarted != null) onStarted(result.RootProcessId);
                if (ResumeThread(process.Thread) == UInt32.MaxValue)
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "Resume owned process");
                while (true) {
                    Observe(job, ids);
                    uint wait = WaitForSingleObject(process.Process, 100);
                    if (wait == 0) break;
                    if (wait != 258) throw new Win32Exception(Marshal.GetLastWin32Error(), "Wait for owned process");
                    // A termination request is not proof of exit. Stop the
                    // observation loop at the same deadline even if Windows
                    // cannot terminate/signal the root; finally performs only
                    // bounded cleanup and leaves TreeEmpty false if unconfirmed.
                    if (elapsed.ElapsedMilliseconds >= maxMilliseconds) {
                        result.TimedOut = true;
                        if (!TerminateJobObject(job, 124))
                            result.Error = "Deadline termination failed: " + Marshal.GetLastWin32Error();
                        break;
                    }
                }
                uint code; Check(GetExitCodeProcess(process.Process, out code), "Read owned process exit");
                result.RootExitCode = code; Observe(job, ids);
                if (ActiveCount(job) != 0) {
                    result.ResidualTreeTerminated = !result.TimedOut;
                    Check(TerminateJobObject(job, 125), "Terminate residual owned descendants");
                }
            } catch (Exception exception) {
                result.Error = exception.Message;
            } finally {
                if (deadline != null) deadline.Dispose();
                lock (gate) {
                    if (process.Process != IntPtr.Zero && !assigned && !TerminateProcess(process.Process, 125))
                        result.Error = "Suspended root termination failed: " + Marshal.GetLastWin32Error();
                    if (job != IntPtr.Zero) {
                        // Termination is scoped to this job only; no name scans,
                        // global Dart kills, guessed ancestry or reused PIDs.
                        TerminateJobObject(job, result.TimedOut ? 124u : 125u);
                        Stopwatch cleanup = Stopwatch.StartNew();
                        try {
                            while (ActiveCount(job) != 0 && cleanup.ElapsedMilliseconds < 5000) Thread.Sleep(20);
                            result.TreeEmpty = ActiveCount(job) == 0;
                        } catch (Exception exception) { result.Error = exception.Message; }
                        CloseHandle(job); job = IntPtr.Zero;
                    }
                    if (process.Process == IntPtr.Zero) result.TreeEmpty = true;
                    else if (WaitForSingleObject(process.Process, 5000) == 0) {
                        uint code;
                        if (GetExitCodeProcess(process.Process, out code)) result.RootExitCode = code;
                    } else {
                        result.TreeEmpty = false;
                        result.Error = "Owned root exit was not confirmed after termination";
                    }
                }
                if (process.Thread != IntPtr.Zero) CloseHandle(process.Thread);
                if (process.Process != IntPtr.Zero) CloseHandle(process.Process);
                if (input != IntPtr.Zero) CloseHandle(input);
                if (output != IntPtr.Zero) CloseHandle(output);
                if (error != IntPtr.Zero) CloseHandle(error);
                int[] observed = new int[ids.Count]; ids.CopyTo(observed); Array.Sort(observed);
                result.ObservedProcessIds = observed;
            }
            return result;
        }
    }
}