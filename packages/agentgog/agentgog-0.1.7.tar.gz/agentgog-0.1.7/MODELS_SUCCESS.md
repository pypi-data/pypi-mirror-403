# Successfully Tested OpenRouter Free Models

Test date: 2026-01-17T15:23:12
Test prompt: "Who are you?"
Total successful: 9/28

| Model ID                                 | Size    | Latency (ms) | Response (truncated)                                                                                                |
|------------------------------------------|---------|--------------|---------------------------------------------------------------------------------------------------------------------|
| `meta-llama/llama-3.3-70b-instruct:free` | 70B     | 6871.37      | I'm an artificial intelligence model known as Llama. Llama stands for "Large Language Model Meta AI."               |
| `google/gemma-3-12b-it:free`             | 12B     | 8409.83      | I'm Gemma, an open-weights AI assistant. I'm a large language model created by the Gemma team at Google DeepMind... |
| `tngtech/deepseek-r1t-chimera:free`      | Unknown | 4958.68      | Greetings! I'm DeepSeek-R1, an artificial intelligence assistant created by DeepSeek. I'm at your service...        |
| `z-ai/glm-4.5-air:free`                  | Unknown | 7906.84      | I'm GLM, a large language model developed by Zhipu AI. I'm designed to understand and generate human-like text...   |
| `google/gemma-3n-e4b-it:free`            | 4B      | 2776.65      | I'm Gemma, an open-weights AI assistant! I'm a large language model created by the Gemma team at Google DeepMind... |
| `google/gemma-3-4b-it:free`              | 4B      | 2674.30      | I'm Gemma, a large language model created by the Gemma team at Google DeepMind. I'm an open-weights model...        |
| `google/gemma-3n-e2b-it:free`            | 2B      | 2424.02      | I'm Gemma, an open-weights AI assistant! I'm a large language model created by the Gemma team at Google DeepMind... |
| `mistralai/devstral-2512:free`           | Unknown | 726.42       | I'm a large language model created by Mistral AI.                                                                   |
| `google/gemini-2.0-flash-exp:free`       | Unknown | 742.31       | I am a large language model, trained by Google.                                                                     |

## Notes

- Sorted by model size (descending), then by latency
- "Unknown" size indicates the model ID does not contain size information in the expected format (-Xb or -eXb)
- Latency is time-to-first-token (TTFT) in milliseconds
- Tests were run with a 15 second timeout and 0.5 second delay between requests
