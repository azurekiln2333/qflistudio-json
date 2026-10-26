# Retained native ownership repair

This source-only repair follows commit d0f3c50 and coordinator notices 767 and 776.
It retires the previous initialized manifest for execution because runner hashes changed.
No native, compiler, SDK or device action ran during this repair.

The original helper closed handles after an uncertain cleanup. The replacement retains the
original root and Job until both root terminal and Jobactive0 are observed. Unknown accounting
or waits remain HOLD. A failed timeout or HOLD cannot become an accepted process later.
HOLD evidence includes the original root creation FILETIME and retained handle values.

The parent treats the validation wrapper as a custodian. Its deadline marks failure and HOLD.
It cannot terminate that live wrapper because the wrapper may retain nested phase Jobs.
Payload phases and publishers can terminate their own exact Jobs. They must retain handles
until terminal and active0. The parent and child records retain the detailed ownership fields.

A recovered HOLD may exceed the total budget. This is a failure and cannot establish a
120-second controls window or a 240-second native window. The original tool invocation must
stay alive while ownership is unresolved. No successor release is permitted during HOLD.

The proposed controls observer preflights six frozen file identities before compilation.
It owns acceptance, one controls custodian, terminal observation and final relay in one call.
Seven synthetic controls are authored. They cover normal exit, payload timeout, custodian
survival, nested holder survival, absent executable, callback failure before resume and a
nonzero publisher. Expected rejection within a control never means process acceptance.

Windows runtime behavior remains UNRUN. Fresh C protocol acceptance and a separate named
controls grant are required. A later native grant also requires a newly bound prepared
manifest. Grant703 remains failed and consumed. Device and all-family acceptance remain open.
