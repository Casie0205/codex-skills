<script setup lang="ts">
import background from '../assets/template_section.png'
import { useSlideContext } from '@slidev/client'

const { $frontmatter } = useSlideContext()
</script>

<template>
  <div
    class="slidev-layout chcnav-section"
    :style="{ backgroundImage: `url(${background})` }"
  >
    <div class="chcnav-section-number">
      {{ $frontmatter.sectionNumber }}
    </div>
    <div class="chcnav-section-copy">
      <h1>{{ $frontmatter.title }}</h1>
      <div class="chcnav-section-body">
        <slot />
      </div>
    </div>
  </div>
</template>
