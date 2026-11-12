#!/usr/bin/env bash
# Convert all text in a print PDF to vector outlines (no fonts needed), keeping CMYK values and images unchanged.
# Usage: ./outline_fonts.sh input.pdf output.pdf   (then re-attach the original OutputIntent, see restore step in history)
gs -q -o "$2" -sDEVICE=pdfwrite -dNoOutputFonts -dCompatibilityLevel=1.7 \
  -sColorConversionStrategy=LeaveColorUnchanged -dAutoRotatePages=/None \
  -dDownsampleColorImages=false -dDownsampleGrayImages=false -dDownsampleMonoImages=false \
  -dAutoFilterColorImages=false -dAutoFilterGrayImages=false \
  -dColorImageFilter=/FlateEncode -dGrayImageFilter=/FlateEncode \
  -dPassThroughJPEGImages=true -dPreserveOverprintSettings=true "$1"
