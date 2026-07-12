title:: LM Studio — Adreno GPU Not Detected Fix (Snapdragon X2 Elite Extreme)
type:: guide
tags:: #LMStudio #Adreno #Snapdragon #WindowsOnARM #LocalAI #Vulkan #Troubleshooting
status:: current
last-updated:: [[2026-07-06]]
hardware:: Snapdragon X2 Elite Extreme · Adreno GPU · Windows 11 ARM64

- # LM Studio — Why the Adreno GPU Isn't Detected (And What to Actually Do)
  collapsed:: false
	- > **The short answer**: As of LM Studio 0.4.x, the app ships **no Vulkan, DirectML, or Adreno GPU runtime** for Windows ARM64. The "0 GPUs detected" message is expected, not a misconfiguration. This guide explains why, and walks through the only currently working path to get Adreno GPU inference.
	- #+BEGIN_WARNING
	  This is confirmed by real-world testing on Snapdragon X Elite (Adreno X1-85, Windows 11 ARM64, LM Studio 0.4.12, May 2026). The Adreno GPU **does** support Vulkan 1.3 — the issue is that LM Studio's bundled runtime does not have a Vulkan backend for ARM64 Windows yet.
	  #+END_WARNING

- ## Part 1 — Diagnosing the "0 GPUs Detected" Message
  collapsed:: false
	- ### Step 1 — Confirm LM Studio really has no GPU runtime
		- Open a **PowerShell** window and run:
		  ```powershell
		  lms runtime get -l
		  ```
		- What you will see (and why each line matters):
			- `llama.cpp-win-arm64` → CPU-only runtime, always present
			- If **no** `vulkan`, `directml`, or `qnn` entry appears in the list → confirmed: LM Studio has no GPU runtime for your platform
		- #+BEGIN_NOTE
		  On Windows x64 machines with NVIDIA cards, `lms runtime get -l` shows a CUDA runtime. On Snapdragon ARM64, that entry simply does not exist yet. This is a LM Studio software gap, not a driver or hardware problem.
		  #+END_NOTE
	- ### Step 2 — Confirm your Adreno GPU *does* support Vulkan (the driver side is fine)
		- Download and install the [Vulkan SDK for Windows](https://vulkan.lunarg.com/sdk/home#windows) — pick the ARM64-compatible installer
		- After install, open PowerShell and run:
		  ```powershell
		  vulkaninfo --summary
		  ```
		- You should see output like this — if you do, your driver is healthy:
		  ```
		  GPU0: Qualcomm(R) Adreno(TM) GPU
		    apiVersion         = 1.3.x
		    driverName         = Qualcomm Technologies Inc. Adreno Vulkan Driver
		    conformanceVersion = 1.3.x.x
		    deviceType         = PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU
		  ```
		- If `vulkaninfo` does **not** list the Adreno device:
			- Go to **Settings → Windows Update → Advanced Options → Optional Updates** and install any Qualcomm driver updates
			- Or visit your OEM's driver page (Lenovo, Dell, ASUS, HP, Microsoft) and install the latest Snapdragon X2 GPU driver package
			- Reboot after installing drivers — Vulkan ICD registration requires a full restart
	- ### Step 3 — Understand what LM Studio's runtime model means
		- LM Studio bundles self-contained "runtimes" — each runtime is a pre-compiled version of `llama.cpp` with a specific GPU backend baked in
		- On Windows ARM64, only the CPU runtime ships today because Qualcomm's GPU compute path (Vulkan or QNN) requires separate compilation work that LM Studio has not yet shipped
		- **This is not something you can fix in LM Studio settings — no toggle, no driver reinstall, no reinstall of LM Studio itself will make the GPU appear**
		- Run `lms runtime get -l` periodically after LM Studio updates to check when a Vulkan or QNN runtime lands for ARM64

- ## Part 2 — The Actual Fix: Run a Vulkan-Enabled llama.cpp Alongside LM Studio
  collapsed:: false
	- > Since LM Studio's bundled runtime has no Vulkan/Adreno backend, you build `llama.cpp` yourself with Vulkan enabled and run it as a standalone server. LM Studio (or any OpenAI-compatible client) can then point to it.
	- #+BEGIN_WARNING
	  **Read the performance section (Part 3) before doing this.** On small models (≤7B Q4), the Adreno Vulkan path may actually be *slower* than LM Studio's CPU runtime for the first few runs due to Vulkan shader compilation overhead. This is not a bug — it's a known Vulkan-on-Adreno characteristic.
	  #+END_WARNING
	- ### Step 1 — Install prerequisites
		- **A. Add ARM64 build tools to Visual Studio**
			- Open **Visual Studio Installer** → find your VS 2022 (or VS 2026 Preview) install → click **Modify**
			- Under **Individual Components**, search for and tick:
				- `MSVC vXXX ARM64 build tools` (the ARM64 variant of the C++ compiler)
				- `Windows 11 SDK`
				- `C++ Clang Compiler for Windows`
				- `MSBuild support for LLVM toolset (clang)`
			- Click **Modify** and wait for install to complete
			- #+BEGIN_NOTE
			  The default "Desktop development with C++" workload only installs x64 libraries. The ARM64 build tools component is separate and easy to miss. Without it, `clang-cl` will compile but fail to link with missing `msvcrt.lib` / `oldnames.lib` errors.
			  #+END_NOTE
		- **B. Install the Vulkan SDK**
			- Download from [vulkan.lunarg.com/sdk/home#windows](https://vulkan.lunarg.com/sdk/home#windows) — use the default install location (`C:\VulkanSDK\<version>\`)
			- Confirm `glslc.exe` is present at `C:\VulkanSDK\<version>\Bin\glslc.exe`
		- **C. Install CMake and Ninja** (if not present)
			- [cmake.org/download](https://cmake.org/download/) — pick the ARM64 Windows installer
			- [ninja-build.org](https://ninja-build.org/) — or install via `winget install Ninja-build.Ninja`
	- ### Step 2 — Clone llama.cpp
		- Open a plain **PowerShell** window (not a VS Developer prompt — you'll set the environment manually):
		  ```powershell
		  git clone https://github.com/ggml-org/llama.cpp
		  cd llama.cpp
		  ```
	- ### Step 3 — Build with Vulkan backend (CRITICAL: use cmd.exe with vcvarsarm64)
		- #+BEGIN_WARNING
		  This step **must** be done in a plain `cmd.exe` shell after calling `vcvarsarm64.bat`. The VS Developer PowerShell provides a mixed/x64 environment that will cause linker failures. The `.bat` environment variables only survive within the same `cmd.exe` process.
		  #+END_WARNING
		- Open **cmd.exe** (not PowerShell, not VS Developer prompt) and run the following block exactly:
		  ```cmd
		  :: 1. Set up the ARM64 native build environment
		  "C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsarm64.bat"
		  
		  :: (If you have VS 2026 Preview or BuildTools, adjust the path accordingly, e.g.:)
		  :: "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsarm64.bat"
		  
		  :: 2. Go into your llama.cpp clone
		  cd C:\llama.cpp
		  mkdir build
		  cd build
		  
		  :: 3. Configure with Vulkan ON, using the ARM64 bundled clang-cl
		  cmake .. -G Ninja ^
		    -DGGML_VULKAN=ON ^
		    -DGGML_CUDA=OFF ^
		    -DGGML_METAL=OFF ^
		    -DVULKAN_SDK="C:\VulkanSDK\1.4.341.1" ^
		    -DCMAKE_C_COMPILER="C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\VC\Tools\Llvm\ARM64\bin\clang-cl.exe" ^
		    -DCMAKE_CXX_COMPILER="C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\VC\Tools\Llvm\ARM64\bin\clang-cl.exe"
		  
		  :: 4. Build
		  ninja -j8
		  ```
		- Adjust the `VULKAN_SDK` path to match your installed version (check `C:\VulkanSDK\` for the actual folder name)
		- The `clang-cl.exe` path uses the **VS-bundled** ARM64 Clang — not a standalone LLVM install. Verify the path exists before running
	- ### Step 4 — Fix the missing OpenMP DLL
		- After the build completes, running any binary will likely fail with:
		  ```
		  libomp140.aarch64.dll was not found
		  ```
		- Fix — copy the DLL from VS redistributables into the build output folder:
		  ```cmd
		  :: Adjust the MSVC version number (14.xx.xxxxx) to match what's installed under your Redist folder
		  copy "C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\VC\Redist\MSVC\14.xx.xxxxx\debug_nonredist\arm64\Microsoft.VC145.OpenMP.LLVM\libomp140.aarch64.dll" "C:\llama.cpp\build\bin\"
		  ```
		- To find the exact path, run:
		  ```powershell
		  Get-ChildItem "C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\VC\Redist\MSVC\" -Recurse -Filter "libomp140.aarch64.dll"
		  ```
	- ### Step 5 — Verify the Adreno GPU is detected
		- In **PowerShell**:
		  ```powershell
		  C:\llama.cpp\build\bin\llama-cli.exe --list-devices
		  ```
		- Expected output — if you see the Adreno device, the build is correct:
		  ```
		  Available devices:
		    Vulkan0: Qualcomm(R) Adreno(TM) GPU (XXXXX MiB, XXXXX MiB free)
		  ```
		- The memory shown is your full unified memory pool (shared between CPU and GPU — this is expected on integrated SoC designs)
	- ### Step 6 — Download a model
		- Install Hugging Face CLI:
		  ```powershell
		  pip install -U "huggingface_hub[cli]"
		  ```
		- Download a Q4_K_S or Q4_K_M GGUF (start small — 3B or 4B):
		  ```powershell
		  huggingface-cli download bartowski/Llama-3.2-3B-Instruct-GGUF Llama-3.2-3B-Instruct-Q4_K_M.gguf --local-dir C:\models
		  ```
		- Or point at a model you already downloaded via LM Studio (models live in `C:\Users\<you>\.lmstudio\models\`)
	- ### Step 7 — Run inference on the Adreno GPU
		- **Option A: Interactive chat**
		  ```powershell
		  C:\llama.cpp\build\bin\llama-cli.exe `
		    -m "C:\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf" `
		    --device Vulkan0 `
		    -ngl 99 `
		    -c 8192 `
		    -t 8 `
		    -cnv
		  ```
		- **Option B: OpenAI-compatible server (so LM Studio or other tools can use it)**
		  ```powershell
		  C:\llama.cpp\build\bin\llama-server.exe `
		    -m "C:\models\Llama-3.2-3B-Instruct-Q4_K_M.gguf" `
		    --device Vulkan0 `
		    -ngl 99 `
		    -c 8192 `
		    --port 8080
		  ```
		- Key flags:
			- `--device Vulkan0` — explicitly select the Adreno GPU device
			- `-ngl 99` — offload up to 99 transformer layers to GPU (use a number ≥ the model's actual layer count to push everything to GPU)
			- `-c 8192` — context window size (reduce to 4096 if you get OOM)
			- `-t 8` — CPU threads used for tokenization/sampling
		- Startup log should confirm GPU offload:
		  ```
		  load_tensors: offloaded 33/33 layers to GPU
		  Vulkan0 model buffer size = XXXX MiB
		  ```

- ## Part 3 — Honest Performance Expectations
  collapsed:: false
	- #+BEGIN_WARNING
	  Real-world testing (Snapdragon X Elite, May 2026) showed that **Vulkan/Adreno was significantly slower than the CPU-only LM Studio runtime for prompt processing (prefill)**. A 4822-token system prompt that took 30–60 seconds on CPU timed out after 10 minutes on Vulkan. Understand why before assuming the GPU path is better.
	  #+END_WARNING
	- ### Why CPU can beat Adreno for LLM inference right now
		- | Factor | Detail |
		  |---|---|
		  | **Vulkan shader compilation** | On the very first run, Vulkan compiles GLSL compute shaders for every unique kernel. This can take several minutes. Subsequent runs use a shader cache and are faster — but first runs are brutally slow. |
		  | **Oryon CPU is very fast for ARM GEMM** | The llama.cpp ARM64 CPU backend uses `DOTPROD`, `MATMUL_INT8`, and `ARM_FMA` instructions. The Oryon cores are competitive with many GPUs on small-model GEMM at Q4 quantization. |
		  | **Adreno is optimized for graphics, not GPGPU** | The Adreno GPU's Vulkan compute path (used for ML workloads) is less mature and less optimized than its graphics pipeline. Compute shader throughput lags behind what you'd expect from a dedicated ML GPU. |
		  | **Unified memory = shared bandwidth** | CPU and GPU share the same ~135 GB/s memory bus. The GPU has no bandwidth advantage over the CPU for generation, which is memory-bandwidth-bound. |
	- ### When Adreno Vulkan can actually help
		- | Scenario | Reasoning |
		  |---|---|
		  | **Short prompts (< 500 tokens)** | Reduces the prefill phase where the compilation overhead dominates |
		  | **Large models (13B+)** | More layers = more parallelism, better GPU utilization |
		  | **Warm shader cache (2nd+ run)** | After the first run warms the shader cache, generation speed improves |
		  | **Generation-heavy workloads** | Short system prompt, long output — shifts work to the generation phase where GPU may edge out CPU |
	- ### The real GPU acceleration path for Snapdragon X
		- The Adreno GPU via Vulkan is a workaround. The **intended** hardware path for ML inference on Snapdragon X is the **Hexagon NPU (45 TOPS)** via **Qualcomm's QNN (Qualcomm Neural Networks) / AI Engine Direct SDK**. This is not available in LM Studio today but is the acceleration path to watch:
			- **Monitor**: `lms runtime get -l` after each LM Studio update — watch for a `qnn` runtime entry
			- **Monitor**: LM Studio's Discord `#announcements` channel and [github.com/lmstudio-ai/lmstudio-releases](https://github.com/lmstudio-ai/lmstudio-releases) changelogs
			- **Monitor**: `r/LocalLLaMA` and Qualcomm developer blog posts for QNN + llama.cpp integration news

- ## Part 4 — Common Build Errors & Fixes
  collapsed:: false
	- | Error | Cause | Fix |
	  |---|---|---|
	  | `msvcrtd.lib` or `oldnames.lib` not found | VS ARM64 build tools not installed | Visual Studio Installer → Modify → add `MSVC vXXX ARM64 build tools` |
	  | `llama.cpp CMakeLists rejects MSVC` | Using `cl.exe` instead of `clang-cl.exe` | Switch compiler to the ARM64 `clang-cl.exe` inside VS installation |
	  | `mainCRTStartup` undefined | Using standalone LLVM's clang-cl in a wrong shell env | Use VS-bundled `clang-cl.exe` inside a `cmd.exe` that has called `vcvarsarm64.bat` |
	  | `libomp140.aarch64.dll was not found` | OpenMP DLL not in PATH | Copy from VS Redist to `build\bin\` as shown in Step 4 |
	  | `llama-server.exe` is 0 bytes | Ninja silently failed link | `del llama-server.exe` then `ninja llama-server` to see the real error |
	  | `--ngl` flag not recognized | Double-dash variant | Use `-ngl` (single dash) or `--n-gpu-layers` |
	  | `Vulkan0` not listed by `--list-devices` | Vulkan ICD not registered | Reboot after GPU driver install; run `vulkaninfo --summary` to confirm driver |

- ## Part 5 — Summary
  collapsed:: false
	- ```
	  ┌─────────────────────────────────────────────────────────────────────┐
	  │  LM Studio "0 GPUs detected" — Decision Tree                       │
	  │                                                                     │
	  │  Is `lms runtime get -l` showing a vulkan/qnn runtime?             │
	  │    YES → Use it (select in Settings → Runtime)                     │
	  │    NO  → LM Studio has no GPU runtime for ARM64 yet                │
	  │           ↓                                                         │
	  │  Does `vulkaninfo --summary` show the Adreno GPU?                  │
	  │    NO  → Update GPU driver (Windows Update or OEM site), reboot    │
	  │    YES → Driver is fine; the gap is in LM Studio                   │
	  │           ↓                                                         │
	  │  Do you need GPU inference now?                                     │
	  │    NO  → Use LM Studio CPU runtime (it's fast, Oryon is good)      │
	  │    YES → Build llama.cpp from source with -DGGML_VULKAN=ON         │
	  │           (follow Part 2 of this guide)                             │
	  └─────────────────────────────────────────────────────────────────────┘
	  ```
	- ### Recommended short-term setup
		- Use **LM Studio + CPU runtime** for day-to-day work — it's stable, fast on Oryon cores, and zero maintenance
		- Use **llama.cpp Vulkan build** only when testing GPU inference or running models too large for comfortable CPU-only inference
		- Check `lms runtime get -l` and LM Studio release notes every few weeks for QNN runtime availability — that will be the real performance jump when it arrives
	- #LMStudio #Adreno #Snapdragon #WindowsOnARM #Vulkan #LocalAI #Troubleshooting
