# CT8 execution deadline test checkpoint

Owner Windows review of checkpoint 8: 1006 backend tests passed, 72 frontend
tests passed, build/audit passed; real CT6 catalogue and hours-clause acceptance
passed both with isolation off and on. The existing Node `DEP0190` warning
remains non-blocking.

Added a direct process-boundary regression test for an actual started child
which exceeds its deadline and must not write a later completion marker.
This specifically targets the possibility of leaving a Windows virtual-
environment interpreter descendant alive after only its launcher stops.
The production path remains opt-in and OFF by default; public resource and
error-precedence review remain OPEN.
