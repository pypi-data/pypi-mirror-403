import vlf4ions.analyse_change_points as acp
import numpy as np


def test_analyse_bp():

    # Common parameters to all tests
    detection_threshold = 100
    amp = 2
    the_time = np.arange(0, 0.5, 0.1)
    quiet_phase = 1
    quiet_amp = 1
    last_time = 0.2
    quiet_p1 = 0
    quiet_breakpoint = 0.2
    quiet = 1

    # Keep track of errors
    errors = []

    # Test 1 - beginning of the flare
    current_time = the_time[-1]
    current_p1 = 120
    phase = np.array([1, 1, 1, 1, 2])
    quiet_now, prev_timedecay, DP_now, DA = acp.analyse_breakpoint(
        current_time,
        current_p1,
        amp,
        phase,
        the_time,
        quiet,
        quiet_phase,
        quiet_amp,
        last_time,
        quiet_p1,
        detection_threshold,
        quiet_p1,
        quiet_breakpoint,
    )
    if quiet_now == 1 or DP_now != 1:
        errors.append("Problem with breakpoint analysis for flare onset")

    # Prepare for test 2
    last_p1 = current_p1
    quiet = quiet_now
    last_time = 0.4
    phase = np.array([1, 1, 1, 1, 2, 2])
    the_time = np.arange(0, 6, 1)/10

    # Test 2 - Flare maximum
    current_p1 = 50
    current_time = the_time[-1]
    quiet_now, prev_timedecay, DP_now, DA = acp.analyse_breakpoint(
        current_time,
        current_p1,
        amp,
        phase,
        the_time,
        quiet,
        quiet_phase,
        quiet_amp,
        last_time,
        last_p1,
        detection_threshold,
        quiet_p1,
        quiet_breakpoint,
    )
    if quiet_now == 1 or DP_now != 1:
        errors.append("Problem with breakpoint analysis for flare maximum")

    # Prepare for test 3
    last_p1 = current_p1
    quiet = quiet_now
    last_time = 0.5
    phase = np.array([1, 1, 1, 1, 2, 2, 1.9, 1.9])
    the_time = np.arange(0, 8, 1)/10

    # Test 3 - Flare decay
    current_p1 = -10
    current_time = the_time[-1]
    quiet_now, prev_timedecay, DP_now, DA = acp.analyse_breakpoint(
        current_time,
        current_p1,
        amp,
        phase,
        the_time,
        quiet,
        quiet_phase,
        quiet_amp,
        last_time,
        last_p1,
        detection_threshold,
        quiet_p1,
        quiet_breakpoint,
    )
    if quiet_now == 1:
        errors.append(
            "Problem with breakpoint analysis for flare decay: declared as quiet"
        )
    if np.abs(prev_timedecay - 0.55) > 0.1:
        errors.append("Problem with breakpoint analysis for flare decay: decay time")

    # Prepare for test 4
    last_p1 = current_p1
    quiet = quiet_now
    last_time = 0.7
    phase = np.array([1, 1, 1, 1, 2, 2, 1.9, 1.9, 1.7, 1.7])
    the_time = np.arange(0, 10, 1)/10

    # Test 4 - Flare decay update
    current_p1 = -5
    current_time = the_time[-1]
    quiet_now, prev_timedecay, DP_now, DA = acp.analyse_breakpoint(
        current_time,
        current_p1,
        amp,
        phase,
        the_time,
        quiet,
        quiet_phase,
        quiet_amp,
        last_time,
        last_p1,
        detection_threshold,
        quiet_p1,
        quiet_breakpoint,
    )
    if DP_now != 0.7:
        errors.append("Problem with flare decay update: wrong DP")
    if quiet_now == 1:
        errors.append(
            "Problem with breakpoint analysis for flare decay update: declared as quiet"
        )
    if np.abs(prev_timedecay - 0.85) > 0.1:
        errors.append(
            "Problem with breakpoint analysis for flare decay update: decay time"
        )

    # Prepare for test 5
    last_p1 = current_p1
    quiet = quiet_now
    last_time = 0.9
    phase = np.array([1, 1, 1, 1, 2, 2, 1.9, 1.9, 1.7, 1.7, 1.3, 1.3])
    the_time = np.arange(0, 12, 1)/10

    # Test 5 - Back to quiet times
    current_p1 = 10
    current_time = the_time[-1]
    quiet_now, prev_timedecay, DP_now, DA = acp.analyse_breakpoint(
        current_time,
        current_p1,
        amp,
        phase,
        the_time,
        quiet,
        quiet_phase,
        quiet_amp,
        last_time,
        last_p1,
        detection_threshold,
        quiet_p1,
        quiet_breakpoint,
    )
    if DP_now != 0:
        errors.append("Problem with bp analysis - back to quiet: DP is not zero")
    if quiet_now == 0:
        errors.append("Problem with bp analysis - does not go back to quiet ")

    # Test 6 - Quiet after quiet
    last_p1 = current_p1
    quiet = quiet_now
    last_time = 0.9
    phase = np.array([1, 1, 1, 1, 2, 2, 1.9, 1.9, 1.7, 1.7, 1.3, 1.3, 1])
    the_time = np.arange(0, 13, 1)/10
    current_p1 = 0
    current_time = the_time[-1]
    quiet_now, prev_timedecay, DP_now, DA = acp.analyse_breakpoint(
        current_time,
        current_p1,
        amp,
        phase,
        the_time,
        quiet,
        quiet_phase,
        quiet_amp,
        last_time,
        last_p1,
        detection_threshold,
        quiet_p1,
        quiet_breakpoint,
    )
    if DP_now != 0:
        errors.append("Problem with bp analysis - quiet after quiet, DP not zeros")
    if quiet_now == 0:
        errors.append("Problem with bp analysis - does not go stay quiet ")

    # Test 7 - Test last quiet was too long ago
    last_p1 = current_p1
    quiet = quiet_now
    last_time = 0.9
    phase = np.array([1, 1, 1, 1, 2, 2, 1.9, 1.9, 1.7, 1.7, 1.3, 1.3, 1, 1])
    the_time = np.arange(0, 14, 1)/10
    current_p1 = -10
    current_time = the_time[-1]
    quiet_now, prev_timedecay, DP_now, DA = acp.analyse_breakpoint(
        current_time,
        current_p1,
        amp,
        phase,
        the_time,
        quiet,
        quiet_phase,
        quiet_amp,
        last_time,
        last_p1,
        detection_threshold,
        quiet_p1,
        quiet_breakpoint,
    )
    if DP_now != 0:
        errors.append(
            "Problem with bp analysis - quiet after quiet, DP not zero if slope is negative"
        )
    if quiet_now == 0:
        errors.append(
            "Problem with bp analysis - does not go stay quiet if new slope is negative"
        )

    # Test 8 - Quiet after quiet, with negative slope
    last_p1 = current_p1
    quiet = 0 # It is first detected as a flare
    last_time = 9 # Last quiet time
    phase = np.array([1, 1, 1, 1, 2, 2, 1.9, 1.9, 1.7, 1.7, 1.3, 1.3, 1, 1])
    the_time = np.arange(0, 14, 1)
    current_p1 = 1
    current_time = 14 # The time now (14 - 9 > 3)
    quiet_now, prev_timedecay, DP_now, DA = acp.analyse_breakpoint(
        current_time,
        current_p1,
        amp,
        phase,
        the_time,
        quiet,
        quiet_phase,
        quiet_amp,
        last_time,
        last_p1,
        detection_threshold,
        quiet_p1,
        quiet_breakpoint,
    )
    if DP_now != 0:
        errors.append(
            "Problem with bp analysis - quiet after two hours, DP not zero"
        )
    if quiet_now == 0:
        errors.append(
            "Problem with bp analysis - quiet after quiet, quiet_now is not 1"
        )


    # assert no error message has been registered, else print messages
    assert not errors, "errors occured:\n{}".format("\n".join(errors))
