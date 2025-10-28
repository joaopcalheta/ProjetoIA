#!/usr/bin/env python3
from time import sleep, time
from ev3dev2.motor import (SpeedPercent, MoveTank, MediumMotor,  # <-- Changed to MediumMotor
                           OUTPUT_A, OUTPUT_B, OUTPUT_C)
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.sensor import INPUT_1

# Initialize the MoveTank using OUTPUT_B and OUTPUT_C
tank_pair = MoveTank(OUTPUT_B, OUTPUT_C)
# motor_a will be initialized in the 'if __name__ == "__main__":' block

def spin_and_scan(sensor, motor_a, duration_seconds=20, speed=50, motor_a_speed=75):
    """
    Spins motors B & C (tank_pair) for a duration.
    While spinning, it checks the ultrasonic sensor.
    If distance < 20cm, it runs motor_a. Otherwise, motor_a is stopped.
    """
    print("Spinning motors and scanning for {} seconds...".format(duration_seconds))

    # Get the current time to mark the start
    start_time = time()

    # 1. Start the spinning motors
    tank_pair.on(left_speed=SpeedPercent(speed * -1), right_speed=SpeedPercent(speed))

    # 2. Start a loop that runs for the desired duration
    try:
        while (time() - start_time) < duration_seconds:
            # 3. Check the sensor distance
            distance_cm = sensor.distance_centimeters
            print("Distance: {:.1f} cm".format(distance_cm))
            # 4. If distance is < 20cm, run motor A.
            if distance_cm < 40:
                print("!!! Object detected! Distance: {:.1f} cm. Running motor A.".format(distance_cm))
                # Run motor A at the specified speed
                motor_a.on(SpeedPercent(motor_a_speed))
            else:
                # 5. If no object is detected (or it's > 20cm), stop motor A.
                motor_a.off()

            # 6. Wait for a very short time
            sleep(0.1)  # Checks 10 times per second

    except Exception as e:
        print("An error occurred during the loop: {}".format(e))
    finally:
        # 7. Stop ALL motors after the loop finishes (or if an error occurs)
        tank_pair.off()
        motor_a.off()
        print("All motors stopped.")

if __name__ == "__main__":
    us_sensor = None
    motor_a = None
    try:
        # Initialize the sensor on INPUT_1
        us_sensor = UltrasonicSensor(INPUT_1)
        print("Ultrasonic sensor connected.")

        # Initialize Motor A
        motor_a = MediumMotor(OUTPUT_A)  # <-- Changed to MediumMotor
        print("Motor A (Medium) connected.")

        # Run the motors for 30 seconds at 20% speed, while scanning
        spin_and_scan(sensor=us_sensor,
                      motor_a=motor_a,
                      duration_seconds=30,
                      speed=20,
                      motor_a_speed=50) # <-- You can set motor A's speed here

    except Exception as e:
        print("An error occurred: {}".format(e))
        print("Making sure all motors are stopped.")
        # Ensure all motors stop even if an error happens
        tank_pair.off()
        if motor_a:
            motor_a.off()