---
name: remotion
description: "Best practices for Remotion - video creation in React. Use whenever dealing with Remotion code for domain-specific knowledge on animations, compositions, audio, 3D, charts, captions, transitions, and more."
metadata: {"nanobot":{"emoji":"🎬","requires":{"bins":["npx"]},"install":[{"id":"npm","kind":"npm","package":"remotion","bins":["npx"],"label":"Install Remotion (npx create-video@latest)"}]}}
---

# Remotion - Video Creation in React

Use this skill whenever you are dealing with Remotion code to obtain domain-specific knowledge.

## Quick Start

```bash
npx create-video@latest
cd my-video
npx remotion studio
```

## Captions

When dealing with captions or subtitles, load the [./rules/subtitles.md](./rules/subtitles.md) file.

## Using FFmpeg

For video operations like trimming or silence detection, load the [./rules/ffmpeg.md](./rules/ffmpeg.md) file.

## Audio Visualization

For spectrum bars, waveforms, bass-reactive effects, load the [./rules/audio-visualization.md](./rules/audio-visualization.md) file.

## Rules Reference

Read individual rule files for detailed explanations and code examples:

| Rule | Description |
|------|-------------|
| [rules/3d.md](rules/3d.md) | 3D content using Three.js and React Three Fiber |
| [rules/animations.md](rules/animations.md) | Fundamental animation skills |
| [rules/assets.md](rules/assets.md) | Importing images, videos, audio, and fonts |
| [rules/audio.md](rules/audio.md) | Audio - importing, trimming, volume, speed, pitch |
| [rules/audio-visualization.md](rules/audio-visualization.md) | Spectrum bars, waveforms, bass-reactive effects |
| [rules/calculate-metadata.md](rules/calculate-metadata.md) | Dynamic composition duration, dimensions, props |
| [rules/can-decode.md](rules/can-decode.md) | Check if video can be decoded by browser |
| [rules/charts.md](rules/charts.md) | Chart and data visualization (bar, pie, line, stock) |
| [rules/compositions.md](rules/compositions.md) | Compositions, stills, folders, default props |
| [rules/display-captions.md](rules/display-captions.md) | Displaying captions in video |
| [rules/extract-frames.md](rules/extract-frames.md) | Extract frames from videos at specific timestamps |
| [rules/ffmpeg.md](rules/ffmpeg.md) | FFmpeg operations (trimming, silence detection) |
| [rules/fonts.md](rules/fonts.md) | Google Fonts and local fonts |
| [rules/get-audio-duration.md](rules/get-audio-duration.md) | Get audio duration in seconds |
| [rules/get-video-dimensions.md](rules/get-video-dimensions.md) | Get video width and height |
| [rules/get-video-duration.md](rules/get-video-duration.md) | Get video duration in seconds |
| [rules/gifs.md](rules/gifs.md) | GIFs synchronized with timeline |
| [rules/images.md](rules/images.md) | Embedding images with Img component |
| [rules/import-srt-captions.md](rules/import-srt-captions.md) | Import SRT caption files |
| [rules/light-leaks.md](rules/light-leaks.md) | Light leak overlay effects |
| [rules/lottie.md](rules/lottie.md) | Lottie animations |
| [rules/maps.md](rules/maps.md) | Maps with Mapbox |
| [rules/measuring-dom-nodes.md](rules/measuring-dom-nodes.md) | Measuring DOM element dimensions |
| [rules/measuring-text.md](rules/measuring-text.md) | Measuring text, fitting to containers |
| [rules/parameters.md](rules/parameters.md) | Parametrizable videos with Zod schema |
| [rules/sequencing.md](rules/sequencing.md) | Sequencing - delay, trim, limit duration |
| [rules/subtitles.md](rules/subtitles.md) | Subtitles and captions |
| [rules/tailwind.md](rules/tailwind.md) | TailwindCSS in Remotion |
| [rules/text-animations.md](rules/text-animations.md) | Typography and text animations |
| [rules/timing.md](rules/timing.md) | Interpolation curves - linear, easing, spring |
| [rules/transitions.md](rules/transitions.md) | Scene transitions |
| [rules/transparent-videos.md](rules/transparent-videos.md) | Rendering with transparency |
| [rules/trimming.md](rules/trimming.md) | Trimming animations |
| [rules/videos.md](rules/videos.md) | Embedding videos - trimming, volume, speed, looping |
