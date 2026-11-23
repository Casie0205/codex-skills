<script setup lang="ts">
import background from '../assets/template_cover.png'
import { useSlideContext } from '@slidev/client'

const { $frontmatter } = useSlideContext()
</script>

<template>
  <div
    class="slidev-layout chcnav-cover"
    :style="{ backgroundImage: `url(${background})` }"
  >
    <div class="chcnav-cover-title">
      {{ $frontmatter.title }}
    </div>
    <div class="chcnav-cover-divider" />
    <div class="chcnav-cover-subtitle">
      {{ $frontmatter.subtitle }}
    </div>
    <div class="chcnav-cover-meta chcnav-cover-meta-left">
      <span>{{ $frontmatter.metaLeftLabel }}</span>
      <strong>{{ $frontmatter.metaLeftValue }}</strong>
    </div>
    <div class="chcnav-cover-meta chcnav-cover-meta-right">
      <span>{{ $frontmatter.metaRightLabel }}</span>
      <strong>{{ $frontmatter.metaRightValue }}</strong>
    </div>
  </div>
</template>
