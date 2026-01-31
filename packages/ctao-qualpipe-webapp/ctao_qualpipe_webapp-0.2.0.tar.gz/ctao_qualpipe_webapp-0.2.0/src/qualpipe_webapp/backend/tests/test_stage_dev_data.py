def test_stage_dev_data_dir(staged_multi_site_data_dir_for_dev):
    """Force-run the staging fixture used for dev/kind deployments."""
    assert staged_multi_site_data_dir_for_dev.exists()
