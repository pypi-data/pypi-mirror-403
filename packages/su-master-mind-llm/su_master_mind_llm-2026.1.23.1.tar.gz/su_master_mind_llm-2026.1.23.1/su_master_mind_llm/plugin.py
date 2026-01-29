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
        # Shared resource for practical4 and practical5
        lotte_dataset = make_pyterrier_dataset_resource(
            "irds:lotte/technology/dev/search",
            "LoTTE technology dev search dataset",
        )

        return {
            "practical2": [
                make_hf_model_resource(
                    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                    "TinyLlama 1.1B chat model",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_hf_model_resource(
                    "distilbert-base-uncased",
                    "DistilBERT base uncased",
                    "AutoTokenizer",
                    "AutoModelForSequenceClassification",
                ),
                make_hf_model_resource(
                    "distilbert-base-uncased-finetuned-sst-2-english",
                    "DistilBERT fine-tuned on SST-2",
                    "AutoTokenizer",
                    "AutoModelForSequenceClassification",
                ),
                make_hf_dataset_resource(
                    "imdb",
                    "IMDB movie review dataset (train)",
                    splits="train",
                ),
            ],
            "practical3": [
                make_hf_model_resource(
                    "Qwen/Qwen2.5-3B-Instruct-AWQ",
                    "Qwen 2.5 3B Instruct (AWQ quantized)",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_hf_model_resource(
                    "Qwen/Qwen2.5-7B-Instruct-AWQ",
                    "Qwen 2.5 7B Instruct (AWQ quantized)",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_hf_model_resource(
                    "HuggingFaceTB/SmolLM2-1.7B-Instruct",
                    "SmolLM2 1.7B Instruct",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
            ],
            "practical4": [lotte_dataset],
            "practical5": [lotte_dataset],
            "practical6": [
                make_hf_model_resource(
                    "openai/clip-vit-base-patch32",
                    "CLIP ViT-base (OpenAI)",
                    "CLIPModel",
                    "CLIPProcessor",
                ),
                make_hf_model_resource(
                    "Qwen/Qwen2.5-3B-Instruct",
                    "Qwen 2.5 3B Instruct (for VLM)",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_hf_model_resource(
                    "Qwen/Qwen2.5-0.5B-Instruct",
                    "Qwen 2.5 0.5B Instruct (for testing)",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                    optional=True,
                ),
                make_hf_dataset_resource(
                    "jxie/flickr8k",
                    "Flickr8k image-caption dataset",
                    splits=["train", "validation", "test"],
                ),
            ],
            "practical7": [
                make_hf_model_resource(
                    "distilgpt2",
                    "DistilGPT-2 (82M params)",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_hf_model_resource(
                    "gpt2",
                    "GPT-2 Small (124M params)",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                ),
                make_hf_model_resource(
                    "gpt2-medium",
                    "GPT-2 Medium (355M params)",
                    "AutoTokenizer",
                    "AutoModelForCausalLM",
                    optional=True,
                ),
                make_hf_dataset_resource(
                    "glue",
                    "GLUE SST-2 dataset (validation)",
                    splits="validation",
                    name="sst2",
                ),
            ],
        }
