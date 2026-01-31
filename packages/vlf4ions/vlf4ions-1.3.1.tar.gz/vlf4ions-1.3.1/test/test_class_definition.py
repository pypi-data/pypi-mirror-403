import vlf4ions.class_definition as cd
import numpy as np

def test_email_alert_update_body():
    test_alert = cd.email_alerts('test_subject', 'test_body', 'test_sender', 'test_password', ['test_recipients'])
    test_alert.update_detection_body('NRK', 0)
    #print(test_alert.body)
    assert((test_alert.body != 'test_body'))


# TODO: test send_email

def test_sliding_median():
    test_array = np.arange(6)
    res = cd.sliding_median(test_array, 3)

    assert(all(res == [1., 2., 3., 4.]))