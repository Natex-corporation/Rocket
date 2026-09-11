# PX4 estimator and firmware bring-up

PX4 officially supports Windows development through WSL2. Keep the PX4 repository separate from
this workbench so its upstream history and submodules remain intact. Pin a reviewed release tag for
each campaign rather than flying an unrecorded `main` checkout.

Inside Ubuntu/WSL2, following the current official PX4 toolchain guide:

```bash
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot
# Check out the team-approved release tag here, then synchronize submodules.
git submodule update --init --recursive

# First prove the upstream software-in-the-loop build.
make px4_sitl gz_x500

# The official Pixhawk 6C hardware target.
make px4_fmu-v6c_default
```

Do not treat the stock aircraft simulation as a rocket validation. For estimator work, connect a
reviewed rocket dynamics model through PX4's supported simulation interface and supply at least
`HIL_SENSOR` and `HIL_GPS`; retain `HIL_STATE_QUATERNION` as truth for error analysis. PX4 SITL
blocks physical actuators while exercising the internal software.

## Integration sequence

1. Run the workbench `imu-demo` and freeze the CSV axis/unit contract.
2. Map simulated truth into the PX4 simulator messages using FRD body axes and NED navigation.
3. Log raw sensors, estimator innovations/status, quaternion, local position, and truth together.
4. Automate pass/fail metrics for nominal, saturation, bias, vibration, timestamp jitter, dropout,
   barometer-port lag, GNSS loss, and power-cycle cases.
5. Build `px4_fmu-v6c_default`, verify the artifact checksum, then repeat the same cases in HIL.
6. Keep actuator outputs disconnected until independent inhibits and fault responses are verified.

The Pixhawk 6C contains two accel/gyro sets, a magnetometer, and an MS5611 barometer. The separate
ADXL375 reference in the BOM covers high-g measurement beyond the flight controller IMUs' useful
range; integrating it with PX4 requires a reviewed driver/interface and timestamp path. It is not a
drop-in sensor merely because it speaks SPI/I²C.

Official references:

- <https://docs.px4.io/main/en/dev_setup/dev_env>
- <https://docs.px4.io/main/en/dev_setup/building_px4>
- <https://docs.px4.io/main/en/flight_controller/pixhawk6c>
- <https://docs.px4.io/main/en/simulation/>
- <https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf>
