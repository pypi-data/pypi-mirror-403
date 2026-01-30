import torch
import torch.nn as nn

from .utils import PositionalEncoding
from .layers import EncoderLayer


def lengths_to_mask(lengths: torch.Tensor, max_len: int) -> torch.Tensor:
    """
    lengths: [B]，每个样本的有效长度
    return:  [B, 1, L] True=有效位置，False=pad
    """
    device = lengths.device
    B = lengths.size(0)
    arange = torch.arange(max_len, device=device).unsqueeze(0).expand(B, max_len)  # [B,L]
    mask = arange < lengths.unsqueeze(1)  # [B,L]
    return mask.unsqueeze(1)              # [B,1,L]


class SignalEncoder(nn.Module):
    """
    Encoder for continuous signals x: [B, C, L]
    Treat time steps as tokens: tokens length = L, token dim = d_model
    """

    def __init__(
        self,
        c_in: int,
        d_model: int = 512,
        d_ffn_hid: int = 2048,
        n_layers: int = 6,
        n_head: int = 8,
        d_k: int = 64,
        d_v: int = 64,
        dropout: float = 0.1,
        n_position: int = 2000,
        proj: str = "conv",      # "conv" | "linear"
        kernel_size: int = 3,
        use_input_ln: bool = True,
    ):
        super().__init__()

        self.d_model = d_model

        # 1) 输入投影：把 [B,C,L] -> [B,L,d_model]
        if proj == "conv":
            # Conv1d: [B,C,L] -> [B,d_model,L]
            padding = kernel_size // 2
            self.in_proj = nn.Sequential(
                nn.Conv1d(c_in, d_model, kernel_size=kernel_size, padding=padding, bias=False),
                nn.Dropout(dropout),
            )
            self.proj_type = "conv"
        elif proj == "linear":
            # Linear: 每个时间点一个向量 [B,L,C] -> [B,L,d_model]
            self.in_proj = nn.Linear(c_in, d_model, bias=False)
            self.proj_type = "linear"
        else:
            raise ValueError("proj must be 'conv' or 'linear'")

        # 2) 位置编码
        self.position_enc = PositionalEncoding(d_model, n_position=n_position)

        # 3) 输入层 norm（你原 Encoder 也有）
        self.dropout = nn.Dropout(dropout)
        self.input_ln = nn.LayerNorm(d_model, eps=1e-6) if use_input_ln else nn.Identity()

        # 4) Encoder stack（完全复用你的 EncoderLayer）
        self.layer_stack = nn.ModuleList([
            EncoderLayer(d_model, d_ffn_hid, n_head, d_k, d_v, dropout=dropout)
            for _ in range(n_layers)
        ])

        # 初始化（Xavier）
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, x: torch.Tensor, src_mask: torch.Tensor = None, return_attns: bool = False):
        """
        x: [B, C, L]
        src_mask: [B, 1, L] True=有效位置，False=pad
        return:
            enc_output: [B, L, d_model]
            (optional) attns list
        """
        B, C, L = x.shape
        attn_list = []

        # 输入投影到 token 表示
        if self.proj_type == "conv":
            h = self.in_proj(x)            # [B, d_model, L]
            enc_output = h.transpose(1, 2) # [B, L, d_model]
        else:
            enc_output = self.in_proj(x.transpose(1, 2))  # [B, L, d_model]

        # 位置编码 + dropout + LN
        enc_output = self.position_enc(enc_output)
        enc_output = self.dropout(enc_output)
        enc_output = self.input_ln(enc_output)

        # Encoder layers
        for layer in self.layer_stack:
            enc_output, attn = layer(enc_output, slf_attn_mask=src_mask)
            if return_attns:
                attn_list.append(attn)

        if return_attns:
            return enc_output, attn_list
        return enc_output,


class B_TransformerSignalClassifier(nn.Module):
    """
    Transformer classifier for signals: x [B, C, L] -> logits [B, n_class]
    """

    def __init__(
        self,
        c_in: int,
        n_class: int,
        d_model: int = 512,
        d_ffn_hid: int = 2048,
        n_layers: int = 6,
        n_head: int = 8,
        d_k: int = 64,
        d_v: int = 64,
        dropout: float = 0.1,
        n_position: int = 2000,
        pooling: str = "mean",   # "mean" | "max" | "cls"
        proj: str = "conv",
        kernel_size: int = 3,
    ):
        super().__init__()
        assert pooling in ["mean", "max", "cls"]

        self.pooling = pooling

        self.encoder = SignalEncoder(
            c_in=c_in,
            d_model=d_model,
            d_ffn_hid=d_ffn_hid,
            n_layers=n_layers,
            n_head=n_head,
            d_k=d_k,
            d_v=d_v,
            dropout=dropout,
            n_position=n_position,
            proj=proj,
            kernel_size=kernel_size,
            use_input_ln=True,
        )

        # 可学习 CLS 向量（embedding 级，直接拼到序列最前面）
        if pooling == "cls":
            self.cls_token = nn.Parameter(torch.zeros(1, 1, d_model))
            nn.init.normal_(self.cls_token, mean=0.0, std=0.02)

        self.head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(d_model, n_class)
        )

    def _pool(self, enc_output: torch.Tensor, src_mask: torch.Tensor) -> torch.Tensor:
        """
        enc_output: [B, L, D]
        src_mask:   [B, 1, L] True=有效位置，False=pad
        return:     [B, D]
        """
        if self.pooling == "cls":
            return enc_output[:, 0, :]

        valid = src_mask.transpose(1, 2)    # [B, L, 1]
        valid_f = valid.float()

        if self.pooling == "mean":
            summed = (enc_output * valid_f).sum(dim=1)      # [B, D]
            denom = valid_f.sum(dim=1).clamp_min(1.0)       # [B, 1]
            return summed / denom

        neg_inf = torch.finfo(enc_output.dtype).min
        masked = enc_output.masked_fill(~valid, neg_inf)
        return masked.max(dim=1).values

    def forward(
        self,
        x: torch.Tensor,
        lengths: torch.Tensor = None,
        src_mask: torch.Tensor = None,
    ) -> torch.Tensor:
        """
        x: [B, C, L]
        lengths: [B]（可选，变长序列）
        src_mask: [B,1,L]（可选，直接给 mask）
        """
        B, C, L = x.shape

        # 1) 构造 mask（True=有效）
        if src_mask is None:
            if lengths is None:
                src_mask = torch.ones((B, 1, L), dtype=torch.bool, device=x.device)
            else:
                src_mask = lengths_to_mask(lengths, L)

        # 2) 如果用 cls pooling：在时间维前面拼一个 token，并更新 mask
        if self.pooling == "cls":
            cls = self.cls_token.expand(B, 1, -1)  # [B,1,D]
            # 先编码原始序列
            enc_output = self.encoder(x, src_mask)[0]  # [B,L,D]
            enc_output = torch.cat([cls, enc_output], dim=1)  # [B,L+1,D]
            cls_mask = torch.ones((B, 1, 1), dtype=torch.bool, device=x.device)
            src_mask = torch.cat([cls_mask, src_mask], dim=2)  # [B,1,L+1]
        else:
            enc_output = self.encoder(x, src_mask)[0]  # [B,L,D]

        feat = self._pool(enc_output, src_mask)  # [B,D]
        logits = self.head(feat)                 # [B,n_class]
        return logits


if __name__ == "__main__":
    # ===== 测试 =====
    B, C, L = 4, 8, 128
    n_class = 5

    x = torch.randn(B, C, L)

    # mean pooling
    model = B_TransformerSignalClassifier(
        c_in=C,
        n_class=n_class,
        d_model=256,
        d_ffn_hid=1024,
        n_layers=4,
        n_head=8,
        d_k=32,
        d_v=32,
        dropout=0.1,
        n_position=2048,
        pooling="mean",
        proj="conv",
        kernel_size=3,
    )
    logits = model(x)
    print("logits:", logits.shape)  # [B, n_class]

    # 变长输入示例
    lengths = torch.tensor([128, 100, 80, 64])
    logits2 = model(x, lengths=lengths)
    print("logits with lengths:", logits2.shape)
