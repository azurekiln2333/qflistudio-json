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
        public long RootCreationFileTime;
        public string HoldEvidencePath;
        public uint? RootExitCode;
        public bool TimedOut;
        public bool ResidualTreeTerminated;
        public bool TreeEmpty;
        public bool RootTerminal;
        public bool JobActiveZero;
        public bool HoldEntered;
        public double HoldSeconds;
        internal long HoldStartedTick;
        public bool HandlesClosed;
        public string CleanupError;
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
        static extern bool GetProcessTimes(IntPtr process, out long creation, out long exit, out long kernel, out long user);
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

        static string JsonString(string value) {
            if (value == null) return "null";
            StringBuilder text = new StringBuilder("\"");
            foreach (char c in value) {
                if (c == '\\' || c == '"') text.Append('\\').Append(c);
                else if (c < 32) text.Append("\\u").Append(((int)c).ToString("x4"));
                else text.Append(c);
            }
            return text.Append('"').ToString();
        }
        static void PublishHold(ProcessResult result, IntPtr job, IntPtr root, string stderr,
            bool custodian, string reason) {
            if (result.HoldEntered) return;
            result.HoldEntered = true;
            result.HoldStartedTick = Stopwatch.GetTimestamp();
            result.Error = "HOLD: " + reason + "; original handles retained. " + result.Error;
            result.HoldEvidencePath = stderr + ".ownership-hold.json";
            string record = "{\"status\":\"HOLD\",\"terminal\":false,\"pass\":false,\"ownerPid\":" +
                Process.GetCurrentProcess().Id + ",\"rootPid\":" + result.RootProcessId +
                ",\"rootCreationFileTime\":" + result.RootCreationFileTime +
                ",\"jobHandle\":" + JsonString(job.ToInt64().ToString("x")) +
                ",\"rootHandle\":" + JsonString(root.ToInt64().ToString("x")) +
                ",\"custodian\":" + (custodian ? "true" : "false") +
                ",\"utc\":" + JsonString(DateTime.UtcNow.ToString("o")) +
                ",\"error\":" + JsonString(result.Error) + "}";
            try {
                using (System.IO.FileStream stream = new System.IO.FileStream(result.HoldEvidencePath,
                    System.IO.FileMode.CreateNew, System.IO.FileAccess.Write, System.IO.FileShare.Read)) {
                    byte[] bytes = Encoding.UTF8.GetBytes(record + "\n");
                    stream.Write(bytes, 0, bytes.Length); stream.Flush(true);
                }
            } catch (Exception exception) {
                result.CleanupError = "HOLD evidence persistence failed: " + exception.Message;
            }
            try { Console.Error.WriteLine("QFLI_OWNED_HOLD " + record); }
            catch (Exception) { /* Retention must survive a broken stderr. */ }
        }

        public static ProcessResult Run(string executable, string[] arguments, string directory,
            string stdout, string stderr, int maxMilliseconds, Action<int> onStarted) {
            return RunCore(executable, arguments, directory, stdout, stderr, maxMilliseconds, onStarted, false);
        }
        public static ProcessResult RunCustodian(string executable, string[] arguments, string directory,
            string stdout, string stderr, int maxMilliseconds, Action<int> onStarted) {
            return RunCore(executable, arguments, directory, stdout, stderr, maxMilliseconds, onStarted, true);
        }
        static ProcessResult RunCore(string executable, string[] arguments, string directory,
            string stdout, string stderr, int maxMilliseconds, Action<int> onStarted, bool custodian) {
            ProcessResult result = new ProcessResult();
            HashSet<int> ids = new HashSet<int>(); object gate = new object();
            IntPtr job = IntPtr.Zero, output = IntPtr.Zero, error = IntPtr.Zero, input = IntPtr.Zero;
            ProcessInfo process = new ProcessInfo(); Timer deadline = null;
            bool assigned = false, resumed = false; Stopwatch elapsed = Stopwatch.StartNew();
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
                long creation, exitTime, kernelTime, userTime;
                Check(GetProcessTimes(process.Process, out creation, out exitTime, out kernelTime, out userTime), "Read exact root creation identity");
                result.RootCreationFileTime = creation;
                Check(AssignProcessToJobObject(job, process.Process), "Assign suspended process to job"); assigned = true;
                int remaining = maxMilliseconds - checked((int)elapsed.ElapsedMilliseconds);
                if (remaining <= 0) { result.TimedOut = true; throw new TimeoutException("Deadline expired before resume"); }
                deadline = new Timer(delegate(object unused) {
                    lock (gate) {
                        if (job != IntPtr.Zero) {
                            result.TimedOut = true;
                            if (!custodian && !TerminateJobObject(job, 124))
                                result.Error = "Deadline termination failed: " + Marshal.GetLastWin32Error();
                        }
                    }
                }, null, remaining, Timeout.Infinite);
                if (onStarted != null) onStarted(result.RootProcessId);
                if (ResumeThread(process.Thread) == UInt32.MaxValue)
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "Resume owned process");
                resumed = true;
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
                        if (custodian) {
                            PublishHold(result, job, process.Process, stderr, true,
                                "custodian execution deadline exceeded; custodian cannot be killed while it may hold nested Jobs");
                            continue;
                        }
                        if (!TerminateJobObject(job, 124))
                            result.Error = "Deadline termination failed: " + Marshal.GetLastWin32Error();
                        break;
                    }
                }
                uint code; Check(GetExitCodeProcess(process.Process, out code), "Read owned process exit");
                result.RootExitCode = code; Observe(job, ids);
                if (!custodian && ActiveCount(job) != 0) {
                    result.ResidualTreeTerminated = !result.TimedOut;
                    Check(TerminateJobObject(job, 125), "Terminate residual owned descendants");
                }
            } catch (Exception exception) {
                result.Error = exception.Message;
            } finally {
                if (deadline != null) {
                    using (ManualResetEvent stopped = new ManualResetEvent(false)) {
                        deadline.Dispose(stopped); stopped.WaitOne();
                    }
                }
                lock (gate) {
                    // The original invocation must remain alive on HOLD. A
                    // custodian that has resumed may own nested handles: neither
                    // its deadline nor this cleanup can terminate its Job/root.
                    // Payload mode may terminate only its own exact Job/root.
                    Stopwatch cleanup = Stopwatch.StartNew();
                    long lastTermination = -1000;
                    bool rootTerminal = process.Process == IntPtr.Zero;
                    bool jobActiveZero = job == IntPtr.Zero;
                    while (true) {
                        // No PID reopening or name-based process scans. All
                        // observations and termination target retained originals.
                        if (cleanup.ElapsedMilliseconds - lastTermination >= 1000) {
                            lastTermination = cleanup.ElapsedMilliseconds;
                            if ((!custodian || !resumed) && job != IntPtr.Zero &&
                                !TerminateJobObject(job, result.TimedOut ? 124u : 125u))
                                result.CleanupError = "Owned Job termination unconfirmed: " + Marshal.GetLastWin32Error();
                            if (process.Process != IntPtr.Zero && (!assigned || (custodian && !resumed)) && !rootTerminal &&
                                !TerminateProcess(process.Process, 125))
                                result.CleanupError = "Suspended unassigned root termination unconfirmed: " + Marshal.GetLastWin32Error();
                        }
                        if (job != IntPtr.Zero) {
                            try { jobActiveZero = ActiveCount(job) == 0; }
                            catch (Exception exception) {
                                jobActiveZero = false;
                                result.CleanupError = "Owned Job accounting unconfirmed: " + exception.Message;
                            }
                        }
                        if (process.Process != IntPtr.Zero) {
                            uint wait = WaitForSingleObject(process.Process, 0);
                            rootTerminal = wait == 0;
                            if (rootTerminal) {
                                uint code;
                                if (GetExitCodeProcess(process.Process, out code)) result.RootExitCode = code;
                                else result.CleanupError = "Terminal root exit code unavailable: " + Marshal.GetLastWin32Error();
                            } else if (wait != 258) {
                                result.CleanupError = "Owned root terminal wait unconfirmed: " + Marshal.GetLastWin32Error();
                            }
                        }
                        result.RootTerminal = rootTerminal;
                        result.JobActiveZero = jobActiveZero;
                        result.TreeEmpty = rootTerminal && jobActiveZero;
                        if (result.TreeEmpty) break;
                        if (cleanup.ElapsedMilliseconds >= 5000 && !result.HoldEntered) {
                            PublishHold(result, job, process.Process, stderr, custodian,
                                "exact root terminal or Jobactive0 remains unconfirmed during cleanup");
                        }
                        Thread.Sleep(result.HoldEntered ? 100 : 20);
                    }
                    if (result.HoldEntered)
                        result.HoldSeconds = (Stopwatch.GetTimestamp() - result.HoldStartedTick) / (double)Stopwatch.Frequency;
                    // Closure is reachable only with independently observed root
                    // terminal AND Job active0. A null Job does not stand in for
                    // the unassigned suspended root's terminal observation.
                    if (job != IntPtr.Zero) {
                        if (!CloseHandle(job)) result.CleanupError = "Close verified empty Job failed: " + Marshal.GetLastWin32Error();
                        job = IntPtr.Zero;
                    }
                }
                bool closed = true;
                if (process.Thread != IntPtr.Zero) closed = CloseHandle(process.Thread) && closed;
                if (process.Process != IntPtr.Zero) closed = CloseHandle(process.Process) && closed;
                if (input != IntPtr.Zero) closed = CloseHandle(input) && closed;
                if (output != IntPtr.Zero) closed = CloseHandle(output) && closed;
                if (error != IntPtr.Zero) closed = CloseHandle(error) && closed;
                result.HandlesClosed = closed && result.TreeEmpty && result.CleanupError == null;
                if (!result.HandlesClosed && result.Error == null)
                    result.Error = "Owned handle closure unconfirmed: " + result.CleanupError;
                int[] observed = new int[ids.Count]; ids.CopyTo(observed); Array.Sort(observed);
                result.ObservedProcessIds = observed;
            }
            return result;
        }
    }
}