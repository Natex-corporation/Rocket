# IMU and guidance workbench

The built-in estimator is intentionally a teaching and interface fixture. It provides a stable
CSV contract, complementary roll/pitch estimate, a two-state vertical Kalman filter, and a
debounced flight-phase state machine. It does **not** provide yaw observability, full navigation,
coning/sculling corrections, redundancy management, or certified deployment logic.

Required log columns:

```text
time_s,ax_m_s2,ay_m_s2,az_m_s2,gx_rad_s,gy_rad_s,gz_rad_s,baro_altitude_m
```

Axes are FRD. Accelerometer values are specific force; a stationary upright sensor reports about
`az=-9.80665 m/s²`. Calibrate scale, bias, axis alignment, temperature response, timing latency,
and vibration sensitivity for the exact assembled electronics stack.

## Production direction

1. Use the RocketPy truth trajectory to synthesize noisy/delayed IMU, barometer, magnetometer,
   and GNSS observations.
2. Feed them through PX4's supported simulation interface and compare EKF2 estimates against truth.
3. Replay real bench and captive-test logs with the same acceptance metrics.
4. Keep recovery deployment on independent, qualified hardware until the experimental system has
   accumulated sufficient evidence and the responsible safety authority accepts the architecture.

Suggested estimator acceptance metrics include attitude error, altitude error, vertical-speed
error, phase-transition timing, estimator innovation consistency, reset count, and behavior under
sensor saturation/dropout. Define numeric limits before looking at test results.

The `guidance` CLI consumes the estimator CSV and computes a transparent ballistic apogee estimate
and phase advisory. It assumes no drag and is therefore an analysis bound, not a deployment
algorithm. Its output is explicitly non-actuating: `MONITOR_ONLY`, `UNDER_TARGET_MONITOR_ONLY`,
`RECOVERY_SYSTEM_REQUIRED`, or `SAFE_AND_LOG` are records for review, never hardware commands.

Guidance development should begin with observation and recovery-support functions (state estimate,
apogee prediction, airbrake simulation). Any actuator path needs independent inhibits, command
limits, timeout-to-safe behavior, range checks, and HIL fault injection before flight approval.
