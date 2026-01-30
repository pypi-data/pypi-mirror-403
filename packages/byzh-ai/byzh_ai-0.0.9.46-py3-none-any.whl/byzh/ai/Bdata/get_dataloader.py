import torch
from torch.utils.data import TensorDataset, DataLoader

def b_get_dataloader_from_tensor(
    X_train, y_train, X_val, y_val, X_test=None, y_test=None,
    batch_size=128,
    num_workers=0,
):
    """
    根据张量构建 DataLoader
    :param X_train, y_train, X_val, y_val, X_test, y_test: torch.Tensor
    :param batch_size: batch 大小
    :param num_workers: DataLoader 的子进程数
    """
    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers
    )

    if X_test is not None and y_test is not None:
        test_dataset = TensorDataset(X_test, y_test)
        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers
        )
        return train_loader, val_loader, test_loader

    return train_loader, val_loader

def b_get_dataloader_from_dataset(
    train_dataset, val_dataset, test_dataset=None,
    batch_size=128, num_workers=0
):
    """
    根据数据集构建 DataLoader
    :param train_dataset, val_dataset, test_dataset: torch.utils.data.Dataset
    :param batch_size: batch 大小
    :param num_workers: DataLoader 的子进程数
    """
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    if test_dataset is not None:
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
        return train_loader, val_loader, test_loader

    return train_loader, val_loader

