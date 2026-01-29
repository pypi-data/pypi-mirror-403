"""LLM course plugin implementation.

This module provides the plugin implementation for the Large Language Models
course as a standalone package.
"""

from typing import Dict, List

from master_mind.plugin import (
    DownloadableResource,
    ExternalCoursePlugin,
    make_pyterrier_dataset_resource,
)
from master_mind.teaching.hf import make_hf_dataset_resource, make_hf_model_resource


class LLMCoursePlugin(ExternalCoursePlugin):
    """Large Language Models course plugin."""

    @property
    def name(self) -> str:
        return "llm"

    @property
    def description(self) -> str:
        return "Large Language Models course"

    @property
    def package_name(self) -> str:
        return "su_master_mind_llm"

    def get_downloadable_resources(self) -> Dict[str, List[DownloadableResource]]:
        return {
            "practical1": [
                make_hf_model_resource(
                    "distilbert-base-uncased",
                    "distilbert-base-uncased",
                    "AutoTokenizer",
                    "AutoModel",
                ),
            ],
            "practical2": [
                make_hf_model_resource(
                    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                    "TinyLlama-1.1B-Chat-v1.0",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_hf_dataset_resource(
                    "imdb",
                    "imdb dataset",
                    splits="train",
                ),
            ],
            "practical3": [
                make_hf_model_resource(
                    "distilbert-base-uncased-finetuned-sst-2-english",
                    "distilbert-base-uncased-finetuned-sst-2-english",
                    "AutoTokenizer",
                    "AutoModelForSequenceClassification",
                ),
                make_hf_dataset_resource(
                    "imdb",
                    "imdb dataset",
                    splits="train",
                ),
            ],
            "practical4": [
                make_hf_model_resource(
                    "HuggingFaceTB/SmolLM2-1.7B-Instruct",
                    "SmolLM2-1.7B-Instruct",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_pyterrier_dataset_resource(
                    "irds:lotte/technology/dev/search",
                    "lotte technology dev search dataset",
                ),
            ],
            "practical5": [
                make_hf_model_resource(
                    "HuggingFaceTB/SmolLM2-1.7B-Instruct",
                    "SmolLM2-1.7B-Instruct",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_pyterrier_dataset_resource(
                    "irds:lotte/technology/dev/search",
                    "lotte technology dev search dataset",
                ),
            ],
            "practical6": [
                make_hf_model_resource(
                    "openai/clip-vit-base-patch32",
                    "clip-vit-base-patch32",
                    "AutoTokenizer",
                    "CLIPModel",
                ),
                make_hf_model_resource(
                    "Qwen/Qwen2.5-3B-Instruct",
                    "Qwen2.5-3B-Instruct",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_hf_model_resource(
                    "Qwen/Qwen2.5-0.5B-Instruct",
                    "Qwen2.5-0.5B-Instruct",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_hf_model_resource(
                    "openai/clip-vit-base-patch32",
                    "clip-vit-base-patch32",
                    "CLIPModel",
                    "CLIPProcessor",
                ),
                make_hf_dataset_resource(
                    "jxie/flickr8k",
                    "jxie/flickr8k dataset",
                ),
            ],
            "practical7": [
                make_hf_model_resource(
                    "HuggingFaceTB/SmolLM2-1.7B-Instruct",
                    "SmolLM2-1.7B-Instruct",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_hf_model_resource(
                    "gpt2",
                    "gpt2",
                    "AutoTokenizer",
                    "GPT2LMHeadModel",
                ),
                make_hf_model_resource(
                    "distilgpt2",
                    "distilgpt2",
                    "GPT2Tokenizer",
                    "GPT2LMHeadModel",
                ),
                make_hf_model_resource(
                    "gpt2",
                    "gpt2",
                    "GPT2Tokenizer",
                    "GPT2LMHeadModel",
                ),
                make_hf_model_resource(
                    "gpt2-medium",
                    "gpt2-medium",
                    "GPT2Tokenizer",
                    "GPT2LMHeadModel",
                    optional=True,
                ),
            ],
        }
