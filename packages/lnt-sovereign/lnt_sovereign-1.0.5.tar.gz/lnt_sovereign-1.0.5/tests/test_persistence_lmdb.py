import os
import shutil

from lnt_sovereign.core.state import LNTStateBuffer


def test_lmdb_persistence():
    db_path = ".test_lnt_state"
    if os.path.exists(db_path):
        pass
        shutil.rmtree(db_path)
    
    # 1. Start buffer and push data
    buffer = LNTStateBuffer(db_path=db_path)
    buffer.push("heart_rate", 72.0)
    buffer.push("heart_rate", 80.0)
    buffer.push("oxygen", 98.0)
    
    # Verify in-session data
    avg = buffer.calculate_average("heart_rate", 60)
    assert abs(avg - 76.0) < 1e-6
    
    buffer.close()
    
    # 2. Re-open and verify persistence
    buffer2 = LNTStateBuffer(db_path=db_path)
    avg2 = buffer2.calculate_average("heart_rate", 60)
    assert abs(avg2 - 76.0) < 1e-6
    
    freq = buffer2.calculate_frequency("oxygen", 60)
    assert freq == 1
    
    buffer2.close()
    
    # Cleanup
    shutil.rmtree(db_path)
    print("LMDB Persistence Test: PASSED")

if __name__ == "__main__":
    test_lmdb_persistence()
