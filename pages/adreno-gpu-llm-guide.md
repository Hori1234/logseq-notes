title:: Running LLMs on the Adreno GPU (Snapdragon X2 Elite Extreme)
type:: guide
tags:: #LLM #Snapdragon #Adreno #WindowsOnARM #LocalAI #Qualcomm
status:: draft
last-updated:: [[2026-07-06]]

- # Running LLMs Locally on the Adreno GPU — Snapdragon X2 Elite Extreme
  collapsed:: false
	- > This guide covers **three distinct frameworks** — **LM Studio**, **Ollama**, and **llama.cpp (raw, Vulkan backend)** — for running local LLMs with GPU acceleration on the **Adreno GPU** integrated into the **Qualcomm Snapdragon X2 Elite Extreme** SoC.
	- #+BEGIN_WARNING
	  The Snapdragon X2 Elite Extreme is a very recent (2025) ARM64 "Windows on Snapdragon" platform. Software support for GPU acceleration on Adreno is **actively evolving**. Some frameworks (notably Ollama) do not yet ship official Adreno GPU acceleration — this is called out explicitly below so you don't waste time chasing unsupported paths.
	  #+END_WARNING

- ## 1. Background — Know Your Hardware
  collapsed:: false
	- **CPU**: Qualcomm Oryon cores (up to 18 cores in the "Extreme" SKU), ARM64 (AArch64) instruction set
	- **GPU**: Adreno (integrated), exposed to Windows via:
		- `DirectX 12` (DirectML)
		- `Vulkan 1.3` (via Adreno Windows driver)
		- `OpenCL` (via Adreno OpenCL driver, used by some ML runtimes)
	- **NPU**: Hexagon NPU (separate from the GPU — accessed via Qualcomm's QNN / AI Engine Direct SDK, **not** covered in depth here since you asked specifically about the **GPU**)
	- #+BEGIN_NOTE
	  On Windows on ARM (WoA), "GPU acceleration" for an LLM almost always means the inference engine's **Vulkan** backend talking to the Adreno Vulkan driver. This is the common thread across all three frameworks below.
	  #+END_NOTE

- ## 2. Shared Prerequisites (do this once)
  collapsed:: false
	- ### 2.1 Update Windows & Adreno GPU drivers
		- id:: prereq-drivers
		- Open **Settings → Windows Update** and install all optional/driver updates
		- Go to **Qualcomm's official driver page** or your OEM's (Lenovo/Dell/Samsung/ASUS/HP) support page and install the latest **Adreno GPU driver** for Snapdragon X2 series
		- Verify the GPU is recognized: open **Task Manager → Performance tab** → confirm "GPU 0 — Qualcomm® Adreno™" appears
	- ### 2.2 Confirm Vulkan support
		- Download **`vulkaninfo`** from the [LunarG Vulkan SDK](https://vulkan.lunarg.com/sdk/home#windows) (ARM64 installer)
		- Run in PowerShell:
		  ```powershell
		  vulkaninfo --summary
		  ```
		- Confirm the Adreno GPU is listed as a `VkPhysicalDevice` with `apiVersion` ≥ 1.3
	- ### 2.3 Install core tooling
		- [ ] Windows Terminal / PowerShell 7+
		- [ ] Git for Windows (ARM64 build)
		- [ ] Python 3.11+ (ARM64 build, from [python.org](https://www.python.org/downloads/windows/), **not** the x64 build under emulation)
		- [ ] (Optional, for building from source) Visual Studio 2022 Community with "Desktop development with C++" + "C++ Clang tools for Windows"

- ## 3. Framework 1 — LM Studio
  collapsed:: false
	- **What it is**: GUI desktop app wrapping `llama.cpp`; easiest on-ramp, ships a native ARM64 build with a selectable Vulkan runtime for GPU offload.
	- id:: lmstudio-steps
	- ### Steps
		- 1. Download the **ARM64 Windows** installer from [lmstudio.ai](https://lmstudio.ai/) — make sure you pick the Snapdragon/ARM build, not the x64 one
		- 2. Install and launch LM Studio
		- 3. Go to **Settings (gear icon) → Runtime**
			- Confirm the active runtime is **"Vulkan llama.cpp (Windows ARM)"** — if a CPU-only runtime is selected, switch it manually
		- 4. Go to the **Discover / Search** tab and download a quantized `GGUF` model sized for on-device use, e.g.:
			- `Llama-3.2-3B-Instruct-Q4_K_M.gguf`
			- `Phi-3.5-mini-instruct-Q4_K_M.gguf`
			- Prefer **Q4_K_M** or **Q4_0** quantization for the best GPU-memory-to-quality tradeoff on integrated graphics
		- 5. Open the **Chat** tab, load the model, then click the **model settings (sliders icon)**
			- Set **GPU Offload** slider to **Max** (or manually set `n_gpu_layers` to the model's full layer count)
			- Set **Context Length** conservatively (4096–8192) since integrated GPU memory is shared with system RAM
		- 6. Start chatting — confirm GPU usage in **Task Manager → Performance → GPU** climbs during generation
	- ### Verification
		- LM Studio's chat window shows **tokens/sec** in the bottom bar after a generation — a healthy Adreno-accelerated run should noticeably outperform the CPU-only runtime on the same model
	- ### Gotchas
		- If LM Studio silently falls back to CPU, reinstall the Vulkan runtime under **Settings → Runtime → Manage Runtimes → Vulkan (ARM64) → Reinstall**
		- Very large models (>8B params, Q4) may exceed practical shared-GPU-memory limits — watch for OOM crashes and drop context length or model size first

- ## 4. Framework 2 — Ollama
  collapsed:: false
	- #+BEGIN_WARNING
	  As of this writing, **Ollama's official Windows ARM64 build does not include a Vulkan (Adreno GPU) backend** — it runs LLMs on **CPU only** on Snapdragon X2 devices. Ollama's GPU acceleration is currently limited to CUDA (NVIDIA), ROCm (AMD), and Metal (Apple Silicon). Treat GPU acceleration here as **experimental / community-patched only**.
	  #+END_WARNING
	- ### 4.1 Standard install (CPU-only, guaranteed to work)
		- 1. Download the **Windows ARM64** installer from [ollama.com/download](https://ollama.com/download)
		- 2. Install, then open PowerShell and pull a small model to sanity-check:
		  ```powershell
		  ollama pull llama3.2:3b
		  ollama run llama3.2:3b
		  ```
		- 3. This will run entirely on the Oryon CPU cores — fast for a CPU, but **not** using the Adreno GPU
	- ### 4.2 Attempting GPU offload (experimental path)
		- id:: ollama-gpu-experimental
		- Check the current status of Vulkan support before investing time:
			- Search open issues/PRs on [github.com/ollama/ollama](https://github.com/ollama/ollama) for `vulkan` and `adreno` to see if a nightly/experimental build has landed
		- If a community Vulkan-enabled fork or build exists:
			- 1. Uninstall the official Ollama build to avoid service conflicts
			- 2. Build/install the Vulkan-enabled fork per its README (this typically means compiling Ollama's bundled `llama.cpp` with `-DGGML_VULKAN=ON`, see [[Framework 3 — llama.cpp]] below for the exact CMake flags)
			- 3. Set the environment variable before starting the server:
			  ```powershell
			  $env:OLLAMA_LLM_LIBRARY = "vulkan"
			  ollama serve
			  ```
		- ### Recommendation
			- id:: ollama-recommendation
			- For **guaranteed Adreno GPU acceleration today**, use **LM Studio** or **raw llama.cpp (Vulkan)** instead of Ollama. Revisit Ollama once official Windows-on-ARM GPU backends ship — check their release notes periodically.

- ## 5. Framework 3 — llama.cpp (raw, Vulkan backend)
  collapsed:: false
	- id:: llamacpp-vulkan
	- **What it is**: The engine underneath both LM Studio and Ollama. Building it yourself gives you the most direct control over Adreno GPU offload and is the best fallback when GUI tools lag behind.
	- ### 5.1 Install build dependencies
		- Install the [Vulkan SDK for Windows](https://vulkan.lunarg.com/sdk/home#windows) (ARM64-compatible installer, default settings)
		- Install [CMake](https://cmake.org/download/) and [Git](https://git-scm.com/downloads/win)
		- Install Visual Studio 2022 with the **C++ Clang tools for Windows** component (needed for the `arm64-windows-llvm` preset)
	- ### 5.2 Clone and build with Vulkan enabled
		- Open a **Developer PowerShell for VS 2022**, then:
		  ```powershell
		  git clone https://github.com/ggml-org/llama.cpp
		  cd llama.cpp
		  cmake -B build -DGGML_VULKAN=ON
		  cmake --build build --config Release -j 8
		  ```
		- For a native Windows-on-ARM optimized build, use the ARM64 LLVM preset instead:
		  ```powershell
		  cmake --preset arm64-windows-llvm-release -DGGML_VULKAN=ON -DGGML_OPENMP=OFF
		  cmake --build build-arm64-windows-llvm-release --config Release -j 8
		  ```
	- ### 5.3 Download a GGUF model
		- Use `huggingface-cli` or download directly, e.g.:
		  ```powershell
		  pip install -U "huggingface_hub[cli]"
		  huggingface-cli download bartowski/Llama-3.2-3B-Instruct-GGUF Llama-3.2-3B-Instruct-Q4_K_M.gguf --local-dir .\models
		  ```
	- ### 5.4 Run inference offloaded to the Adreno GPU
		- ```powershell
		  .\build\bin\Release\llama-cli.exe -m .\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf -ngl 100 -c 8192 -t 8 -cnv
		  ```
		- Flag reference:
			- `-ngl 100` — offload up to 100 transformer layers to GPU (use a number ≥ the model's total layer count to push everything onto the Adreno GPU)
			- `-c 8192` — context window size
			- `-t 8` — CPU threads used for the non-offloaded portion (tokenizer, sampling)
			- `-cnv` — interactive conversation mode
		- You can also launch the built-in OpenAI-compatible server for use with other apps:
		  ```powershell
		  .\build\bin\Release\llama-server.exe -m .\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf -ngl 100 -c 8192 --port 8080
		  ```
	- ### 5.5 Verify GPU offload is active
		- On startup, `llama-cli`/`llama-server` logs a device table — confirm it lists the **Adreno** Vulkan device and shows non-zero layers assigned to it (not `CPU`)
		- Watch **Task Manager → Performance → GPU** during generation to confirm utilization

- ## 6. Framework Comparison
  collapsed:: false
	- | Framework | GPU Backend | Setup Difficulty | Adreno GPU Support | Best For |
	  |---|---|---|---|---|
	  | **LM Studio** | Vulkan (bundled) | Easy (GUI) | ✅ Supported | Beginners, quick local chat UI |
	  | **Ollama** | Vulkan | Easy (CLI) | ⚠️ CPU-only officially; GPU experimental | Familiar `ollama run` workflow, API compatibility |
	  | **llama.cpp** | Vulkan (self-built) | Advanced (build from source) | ✅ Supported, most control | Power users, servers, custom integrations |

- ## 7. Troubleshooting
  collapsed:: false
	- **Model loads but runs slowly / no GPU usage in Task Manager**
		- Confirm `-ngl` (or the LM Studio GPU-offload slider) is set above 0
		- Confirm the Adreno driver version supports Vulkan 1.3 (`vulkaninfo --summary`)
	- **Out-of-memory / crash on load**
		- Drop to a smaller quantization (Q4_K_M → Q4_0 → Q3_K_M)
		- Reduce `-c` (context length)
		- Try a smaller parameter-count model (7B → 3B)
	- **`vulkaninfo` doesn't list the Adreno device**
		- Update GPU drivers via Windows Update or OEM support site
		- Reboot after driver install — Vulkan ICD registration sometimes requires it
	- **Build fails on `arm64-windows-llvm-release` preset**
		- Ensure "C++ Clang tools for Windows" and "MSBuild support for LLVM toolset (clang)" are installed via Visual Studio Installer, not just the base C++ workload

- ## 8. References
  collapsed:: false
	- [LM Studio](https://lmstudio.ai/)
	- [Ollama](https://ollama.com/)
	- [llama.cpp (ggml-org)](https://github.com/ggml-org/llama.cpp)
	- [Vulkan SDK](https://vulkan.lunarg.com/sdk/home#windows)
	- #LLM #Adreno #Snapdragon #WindowsOnARM #Vulkan #LocalAI
