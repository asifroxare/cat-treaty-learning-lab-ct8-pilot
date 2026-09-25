# CT8 checkpoint 10 — Windows watchdog evidence

Claude's second review found that the orphan test did not establish process
death or cover a Windows descendant. The watchdog now fails closed if the
spawned child's parent sentinel is missing. When the parent dies, the watchdog
requests a Windows process-tree kill for its own PID. Tests assert that the
calculation PID is no longer running and, on Windows, that a child-launched
descendant PID also exits without writing a delayed marker.

The owner previously verified checkpoint 9 on Windows: 7 targeted tests and
1010 backend tests passed. The additions in this checkpoint have not been run
on Windows yet. All remaining launch blockers in the review disposition stay
open. Neither frozen actuarial calculations nor React were edited.
