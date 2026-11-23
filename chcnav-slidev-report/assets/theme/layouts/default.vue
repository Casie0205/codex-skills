<script setup lang="ts">
import background from '../assets/template_content.png'
import logo from '../assets/chcnav-logo.png'
import { useSlideContext } from '@slidev/client'

const { $frontmatter } = useSlideContext()
</script>

<template>
  <div
    class="slidev-layout chcnav-content"
    :style="{ backgroundImage: `url(${background})` }"
  >
    <img class="chcnav-content-logo" :src="logo" alt="CHCNAV">
    <header class="chcnav-content-header">
      <h1 v-if="$frontmatter.title">
        {{ $frontmatter.title }}
      </h1>
      <p v-if="$frontmatter.subtitle">
        {{ $frontmatter.subtitle }}
      </p>
    </header>
    <main class="chcnav-content-body" :class="$frontmatter.bodyClass">
      <slot />
    </main>
  </div>
</template>
