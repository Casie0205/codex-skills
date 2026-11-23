<script setup lang="ts">
import background from '../assets/template_content.png'
import logo from '../assets/chcnav-logo.png'
import { useSlideContext } from '@slidev/client'

const { $frontmatter } = useSlideContext()
</script>

<template>
  <div
    class="slidev-layout chcnav-split"
    :class="[$frontmatter.split, $frontmatter.class]"
    :style="{ backgroundImage: `url(${background})` }"
  >
    <img class="chcnav-page-logo" :src="logo" alt="CHCNAV">
    <header class="chcnav-content-header">
      <h1 v-if="$frontmatter.title">
        {{ $frontmatter.title }}
      </h1>
      <p v-if="$frontmatter.subtitle">
        {{ $frontmatter.subtitle }}
      </p>
    </header>
    <main class="chcnav-split-body">
      <section class="chcnav-split-left">
        <slot name="left" />
      </section>
      <section class="chcnav-split-right">
        <slot name="right" />
      </section>
    </main>
  </div>
</template>
