realtime_status
minute_summary
overall_summary
meta

ex.payload

{
 "type":"realtime_status",
 "posture":"turtle_neck",
 "score":83,
 "loadcell_balance":76,
 "neck_tof":42,
 "spine_tof":68
}

APP -> RPi

submit_profile
select_profile
start_measurement
stop_measurement

RPi -> APP

realtime_status
minute_summary
overall_summary
meta