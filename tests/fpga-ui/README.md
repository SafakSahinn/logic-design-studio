# FPGA build & program: click tests

These scripts click through the FPGA "Build & program" panel (map dialog → *Build & program* tab, and the
*FPGA project* tab of the HDL window) in the running app over the Chrome DevTools Protocol. They are not part of
the build. Run them by hand after you change `src/fpga/ui`, `src/fpga/flow`, `src/tools` or `electron/toolRunner.cjs`.

You need Node 22 or newer (it has a built-in `WebSocket`). For the desktop runs you also need oss-cad-suite
(yosys, nextpnr-ecp5, ecppack, openFPGALoader), GHDL, and for the Xilinx 7-series runs the openXC7 package
(Apio's build, `apio-openxc7-<platform>-<date>.tgz` from github.com/FPGAwars/tools-openxc7: nextpnr-xilinx,
fasm2frames, xc7frames2bit and the Project X-Ray database). fasm2frames is a Python program; the app runs it with
the oss-cad-suite's Python (`lib/python3.exe`), found next to yosys. No FPGA board needs to be connected. Without a board,
programming and detection fail with the "no programming cable" message, and the tests expect that message.

| Script | What it checks |
| --- | --- |
| `build_click.mjs <tr\|en> <desktop\|web> [prefix]` | Mapping on GECKO5, build, log, steps, bitstream download (web: the file is really saved), detect/program (desktop), stale bitstream after a language change, VHDL through GHDL, cancel, the HDL-window panel. `QUICK=1` runs the build (and the web download) only. |
| `xc7_click.mjs <tr\|en> <desktop\|web> [prefix]` | Xilinx 7-series (6j-6). Desktop: BASYS3 builds through yosys, nextpnr-xilinx, fasm2frames and xc7frames2bit; the step names show the tools; detect and program use `-b basys3` and fail with "no cable"; on PYNQ-Z2 (Zynq) the flash target is disabled and the build works. Web: the panel says openXC7 runs only in the desktop app, and GECKO5 still builds. |
| `desktop_extra_click.mjs <tr\|en>` | Desktop only. The panel keeps its run, log and bitstream across tab switches. Cancel is disabled during a flash write. Reloading the page while the native flash question is open closes the question and frees openFPGALoader. |
| `snap.mjs` / `restore_exact.mjs` | Save the app's localStorage before the tests and restore it exactly afterwards. The tests change the language, the board mapping and the open sheet. |

Screenshots, downloads and the localStorage backup go to `OUT_DIR` (default: `%TEMP%\lds-fpga-ui`).
`CDP_PORT` selects the app (default 9345).

## Desktop (Electron, native tools)

```sh
# 1. dev server (keep running)
npx vite --port 5173 --strictPort
# 2. the app, with the tools on PATH and a debugging port
OSS=/c/Users/<you>/Tools/eda/oss-cad-suite
export PATH=$OSS/bin:$OSS/lib:/c/Users/<you>/Tools/eda/ghdl/bin:/c/Users/<you>/Tools/eda/openxc7/bin:$PATH
NODE_ENV=development npx electron . --remote-debugging-port=9345
# 3. the tests
cd tests/fpga-ui
export CDP_PORT=9345
SNAP_DELAY=8000 node snap.mjs                # once, before anything else
node build_click.mjs tr desktop e            # expect 39 passed
node build_click.mjs en desktop e
node xc7_click.mjs tr desktop x              # expect 30 passed
node xc7_click.mjs en desktop x
node desktop_extra_click.mjs tr              # expect 14 passed
node desktop_extra_click.mjs en
OPEN_URL='http://localhost:5173/?preset=t_flip_flop_counter#circuit-simulator' QUICK=1 node build_click.mjs tr desktop ec   # a sequential design
node restore_exact.mjs                       # must print "keys same: true | ... none"
```

Close the app afterwards, for example over CDP with `Browser.close`.

## Web (WASM tools)

```sh
# in the web repository
npx vite --port 5174 --strictPort
# a headless Chrome with its own profile (the WASM tools are cached there after the first run)
chrome --headless=new --mute-audio --remote-debugging-port=9346 --user-data-dir=<scratch>/chrome-prof http://localhost:5174/
# the tests (OPEN_URL is required: the site opens on its home page)
export CDP_PORT=9346 OPEN_URL='http://localhost:5174/#circuit-simulator'
node build_click.mjs tr web w                # expect 31 passed
node build_click.mjs en web w
node xc7_click.mjs tr web w                  # expect 11 passed
OPEN_URL='http://localhost:5174/?preset=t_flip_flop_counter#circuit-simulator' QUICK=1 node build_click.mjs en web wc
```

On a fresh profile the first build asks to download the WASM tools (about 60 MB). The script agrees and waits up
to 15 minutes. The headless profile is a separate one, so the user's own browser data is not touched.

## Notes

- `lds.language` is set only after the app's page is open, because `about:blank` is a different origin.
- The board mapping is not kept across a reload in a test profile. The scripts map the board again each time
  (GECKO5_EDUCATION, then *Suggest*).
- On the web, VHDL is synthesized from the same Verilog, because GHDL has no WASM build. Switching to VHDL there
  therefore keeps the bitstream current, and the test expects that.
- The flash "declined" message is covered by a unit test of `src/fpga/ui/buildMessages.ts`, not by a click. The
  native question cannot be clicked over CDP.
