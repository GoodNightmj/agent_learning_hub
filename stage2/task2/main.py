from stage2.task2.file_tool import read_file

if __name__ == "__main__":
    # 测试 read_file 函数
    # Case 1：正常文件
    print("Case 1: 正常文件")
    print(read_file(
        "stage2/task2/data/note.txt",
        "stage2/task2/data"
    ))

    # Case 2：不存在
    print("Case 2: 不存在的文件")
    print(read_file(
        "stage2/task2/data/not_exist.txt",
        "stage2/task2/data"
    ))

    # Case 3：传入目录
    print("Case 3: 传入目录")
    print(read_file(
        "stage2/task2/data",
        "stage2/task2/data"
    ))

    # Case 4：越界读取
    print("Case 4: 越界读取")
    print(read_file(
        ".env",
        "stage2/task2/data"
    ))
    print("case 4: 越界读取")
    print(read_file(
        "stage2/task2/data/note.txt",
        "stage2/task2/data",
        max_chars=10
    ))