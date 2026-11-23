<script setup lang="ts">
import background from '../assets/template_closing.png'
import { useSlideContext } from '@slidev/client'

const { $frontmatter } = useSlideContext()
</script>

<template>
  <div
    class="slidev-layout chcnav-end"
    :style="{ backgroundImage: `url(${background})` }"
  >
    <div class="chcnav-end-title">
      {{ $frontmatter.title || '感谢观看！' }}
    </div>
    <div class="chcnav-end-copy">
      <slot />
    </div>
  </div>
</template>
