from agp_remote_yam.identity import measured_timing


def test_timing_uses_matched_home_sample_not_a_later_worker_event():
    timing=dict(server_received_at=100,run_clicked_at=100,page_entered_at=90,
                home_completed_at=112,home_evidence='matched settled startup feedback')
    result=measured_timing(timing,dict(time=127))
    assert result['run_to_motion_s']==27
    assert result['home_to_measured_completion_s']==15
    assert result['measured_completion_within_limits'] is True
    assert result['outcome']=='measured_motion_visual_timing_unverified'
    late=measured_timing(timing,dict(time=130.1))
    assert late['measured_completion_within_limits'] is False


def test_missing_home_does_not_create_a_timing_pass():
    result=measured_timing(dict(server_received_at=100,run_clicked_at=100,page_entered_at=90),dict(time=110))
    assert result.get('home_to_measured_completion_s') is None
    assert result.get('measured_completion_within_limits') is None
