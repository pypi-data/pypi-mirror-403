import h5py

def b_print_h5py(filepath):
    last_top_level = None  # 顶层组名

    def print_structure(name, obj):
        nonlocal last_top_level # 修改外部（非全局）作用域中的变量
        top_level = name.split("/")[0]  # 获取顶层组名
        if last_top_level is not None and top_level != last_top_level:
            print()  # 顶层组切换时打印空行
        last_top_level = top_level

        if isinstance(obj, h5py.Dataset):
            print(f"[Dataset] {name}, shape={obj.shape}, dtype={obj.dtype}")
        elif isinstance(obj, h5py.Group):
            print(f"[Group] {name}")

    with h5py.File(filepath, "r") as f:
        f.visititems(print_structure)

if __name__ == '__main__':
    b_print_h5py("shd_train.h5")
