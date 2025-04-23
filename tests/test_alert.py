from utils import seconds_to_slurm_time_format
from utils import add_dividers
from utils import gpus_per_job


def test_seconds_to_slurm_time_format():
    assert seconds_to_slurm_time_format(100) == "00:01:40"
    assert seconds_to_slurm_time_format(1000) == "00:16:40"
    assert seconds_to_slurm_time_format(10000) == "02:46:40"
    assert seconds_to_slurm_time_format(100000) == "1-03:46:40"

def test_add_dividers():
    df_str = "x y\n1 1\n2 2\n3 3"
    title = "points"
    actual = add_dividers(df_str, title, pre="")
    expected = "points\n------\nx y\n------\n1 1\n2 2\n3 3\n------\n"
    assert actual == expected

def test_gpus_per_job():
    assert gpus_per_job("") == 0
    assert gpus_per_job("UNKNOWN") == 0
    assert gpus_per_job("gres/gpu=x") == 0
    assert gpus_per_job("billing=8,cpu=4,mem=16G,node=1") == 0
    assert gpus_per_job("billing=112,cpu=112,gres/gpu=0,mem=33600M,node=1") == 0
    assert gpus_per_job("billing=112,cpu=112,gres/gpu=2,mem=33600M,node=1") == 2
    assert gpus_per_job("billing=112,cpu=112,gres/gpu=32,mem=33600M,node=2") == 32
    assert gpus_per_job("billing=112,cpu=112,gres/gpu=320,mem=33600M,node=80") == 320
