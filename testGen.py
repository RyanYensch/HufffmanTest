import subprocess
import sys
import random
import shutil
import string
import filecmp
import resource
from pathlib import Path


folder = "generateTestResults/"
refrence = "/web/cs2521/25T1/ass/ass1/references/encodingLength"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def CompileFiles(san_type = "msan"):
    if (san_type != "asan" and san_type != "msan" and san_type != "nosan"):
        print("Invalid Sanitation Type: [msan, asan, nosan]")
    try:
        subprocess.run(["make", "clean"])
        subprocess.run(["make", san_type])
    except:
        print("Make sure this file is placed in your Huffman Trees base directory")
        exit(1)

def makeFile(filename, minsize, maxsize, unicode):
    size = random.randint(minsize, maxsize)
    if (unicode == "Y"):
        pool = ''.join(chr(i) for i in range(sys.maxunicode + 1) if chr(i).isprintable()) + " \n\t"
    else:
        pool = string.ascii_letters + string.digits + string.punctuation + " \n\t"
    text = ''.join(random.choices(pool, k=size))
    
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)



def check_tree_encoding_length(input_file, tree_file):
    try:   
        result_minimal = subprocess.run(
            [refrence, input_file],
            capture_output=True,
            text=True,
            check=True
        )
        
    except subprocess.CalledProcessError as e:
        print("Error running reference program for minimal encoding length:", e)
        return False
    
    output_minimal = result_minimal.stdout.strip()
    try:
        minimal_length = int(output_minimal.split(":")[-1].strip())
    except Exception as e:
        print("Error parsing minimal encoding length:", e)
        return False

    try:
        result_tree = subprocess.run(
            [refrence, input_file, tree_file],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("Error running reference program for tree encoding length:", e)
        return False

    output_tree = result_tree.stdout.strip()
    try:
        tree_length = int(output_tree.split(":")[-1].strip())
    except Exception as e:
        print("Error parsing tree encoding length:", e)
        return False

    if minimal_length == tree_length:
        return True, 0, 0
    else:
        return False, minimal_length, tree_length



def makeTree(path):
    command = ["./encode", f"{path}input.txt", f"{path}tree.tree"]
    try:
        subprocess.run(command)
        return check_tree_encoding_length(f"{path}input.txt", f"{path}tree.tree")
    except:
        return False, 0, 0

def encode(path):
    command = ["./encode", f"{path}input.txt", f"{path}tree.tree", f"{path}encoded.enc"]
    
    start_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        subprocess.run(command, check= True)
    except:
        return False, None
    
    end_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    user_time = end_usage.ru_utime - start_usage.ru_utime
    system_time = end_usage.ru_stime - start_usage.ru_stime
    return True, user_time + system_time

def decode(path):
    command = ["./decode", f"{path}tree.tree", f"{path}encoded.enc", f"{path}decoded.txt"]
    
    start_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        subprocess.run(command, check=True)
    except:
        return False, None

    end_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    user_time = end_usage.ru_utime - start_usage.ru_utime
    system_time = end_usage.ru_stime - start_usage.ru_stime
    return True, user_time + system_time

def test(path):
    treeState, minimal, actual = makeTree(path)
    if (not treeState):
        return False, 0, minimal, actual

    encodeState, time1 = encode(path)
    decodeState, time2 = decode(path)
    time = max(time1, time2)
    
    if (not encodeState or not decodeState):
        return False, time, minimal, actual
    
    if (time > 5):
        return False, time, minimal, actual
    
    return filecmp.cmp(f"{path}input.txt", f"{path}decoded.txt", shallow=False), time, minimal, actual

def runTests(testCount, minsize = 0, maxsize = 1000000, unicode = "Y"):
    directory_path = Path(folder)
    directory_path.mkdir(parents=True, exist_ok=True)

    # Iterate over all the files and subdirectories in the directory
    for file_path in directory_path.iterdir():
        try:
            if file_path.is_dir():
                shutil.rmtree(file_path)  # Remove subdirectories
            else:
                file_path.unlink()  # Remove files
        except Exception as e:
            print(f"Error removing {file_path}: {e}")
    
    correct = 0
    
    for i in range(1, testCount + 1):
        
        sub_path = directory_path / f'Test{i}'
        sub_path.mkdir(parents=True, exist_ok=True)
        
        try:
            makeFile(f"{sub_path}/input.txt", minsize, maxsize, unicode)
        except:
            print("failed to generate text")
            exit(1)
        
        print(f"Test {i}: ", end="")
        result, time, minimal, actual = test(f"{sub_path}/")
        if (result == True): 
            print(f"{bcolors.OKGREEN}Passed.{bcolors.ENDC}", end = "")
            print(f" Time (User + System): {'{:.2}'.format(time)} seconds.")
            correct += 1
            try: 
                for file_path in sub_path.iterdir():
                    file_path.unlink()
                shutil.rmtree(sub_path)
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
        else:
            print(f"{bcolors.FAIL}Failed.{bcolors.ENDC}", end="") 
            print(f" Time (User + System): {'{:.2}'.format(time)} seconds." if time > 5 else "", end="")
            print(f" Tree Encoding Length Incorrect, Minimal: {minimal}, Your Tree: {actual}" if minimal != actual else "", end="")
            print("")
    
    return correct
    


if __name__ == "__main__":
    print("Running Test for tasks 1,3,4")
    minimum = 0
    maximum = 500000
    useUnicode = "Y"
    if (len(sys.argv) == 2):
        CompileFiles()
        testCount = int(sys.argv[1])
    elif (len(sys.argv) == 3):
        CompileFiles(sys.argv[2])
        testCount = int(sys.argv[1])
    elif (len(sys.argv) == 4):
        CompileFiles(sys.argv[2])
        testCount = int(sys.argv[1])
        minimum = int(sys.argv[3])
    elif (len(sys.argv) == 5):
        CompileFiles(sys.argv[2])
        testCount = int(sys.argv[1])
        minimum = int(sys.argv[3])
        maximum = int(sys.argv[4])
    elif (len(sys.argv) == 6):
        CompileFiles(sys.argv[2])
        testCount = int(sys.argv[1])
        minimum = int(sys.argv[3])
        maximum = int(sys.argv[4])
        useUnicode = (sys.argv[5]).upper()
        if (useUnicode != "Y" and useUnicode != "N"):
            print(useUnicode)
            print("To change the usage of unicode it must be Y or N. By default unicode is enabled")
            exit(1)
    else:
        print("Usage: python3 testGen.py [Number of Tests] *Optional*[msan/asan/nosan] *Optional*[Minumum Length of Characters] *Optional*[Maximum Length of Characters] *Optional*[Unicode: Y/N]")
        exit(1)
    
       
    
    correct = runTests(testCount, minimum, maximum, useUnicode)
    print(f"{bcolors.OKGREEN}{correct} Passed{bcolors.ENDC} and ", end = "")
    print(f"{bcolors.FAIL}{testCount - correct} Failed.{bcolors.ENDC}")
    percent = '{:.3%}'.format(correct/testCount)
    color = bcolors.OKGREEN if correct == testCount else bcolors.FAIL
    print(f"{color}Percent: {percent}")
    if (correct == 0):
        print("These Tests will only work if you have completed Tasks 1,2,3,4")
