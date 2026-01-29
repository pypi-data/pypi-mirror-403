# Copyright (c) 2026 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
from typing import Generator
import torch


@torch.no_grad()
def autoregressive_language_model_generate(
    model,  # type: torch.nn.Module
    input_ids,  # type: torch.LongTensor
    attention_mask,  # type: torch.BoolTensor
):
    # type: (...) -> Generator[torch.Tensor, torch.Tensor, None]
    """
    A generator-based, stateless autoregressive inference loop for language models compatible with HuggingFace's Transformers API. At each step, it yields logits from the model and expects the caller to send back the predicted next tokens. Easily integrates into custom sampling strategies (greedy, beam, top-k/p, etc).

    Args:
        `model` (`torch.nn.Module`): A language model compatible with HuggingFace's Transformers API. Must accept `input_ids`, `attention_mask`, and `position_ids`.
        `input_ids` (`torch.LongTensor`): Token indices to start generation. Shape `(batch_size, seq_len)`.
        `attention_mask` (`torch.BoolTensor`): Attention mask indicating which indices are valid input (1) vs padding (0). Shape `(batch_size, seq_len)`.

    Yields:
        `torch.FloatTensor`: Logits from the model for next token prediction. Shape `(batch_size, seq_len, vocab_size)`.

    Note:
        The caller is responsible for sending back the predicted next tokens. Shape `(batch_size,)`.
    """
    while True:
        # Fully recompute position_ids for new length
        position_ids = attention_mask.long().cumsum(-1) - 1
        position_ids.masked_fill_(attention_mask == 0, 1)

        logits = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
        )

        next_tokens = yield logits

        input_ids = torch.cat(
            [input_ids, next_tokens[:, None]],
            dim=-1
        )
        attention_mask = torch.cat(
            [
                attention_mask,
                attention_mask.new_ones(
                    (attention_mask.shape[0], 1)
                )
            ],
            dim=-1
        )
