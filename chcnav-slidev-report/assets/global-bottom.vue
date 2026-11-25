<script setup lang="ts">
import { useDrawings, useNav } from '@slidev/client'
import { onBeforeUnmount, onMounted } from 'vue'

const { next, prev, isPrintMode } = useNav()
const { isDrawing } = useDrawings()

const INTERACTIVE_SELECTOR = [
  'a',
  'audio',
  'button',
  'details',
  'input',
  'label',
  'select',
  'summary',
  'textarea',
  'video',
  '[contenteditable="true"]',
  '[data-no-slide-navigation]',
  '[role="button"]',
  '[role="slider"]',
  '[role="tab"]',
].join(',')

let wheelLockedUntil = 0
let wheelDelta = 0

function isInPresentation(target: EventTarget | null): target is HTMLElement {
  return target instanceof HTMLElement && Boolean(target.closest('#slide-container'))
}

function shouldIgnore(target: EventTarget | null) {
  return !(target instanceof HTMLElement)
    || !isInPresentation(target)
    || Boolean(target.closest(INTERACTIVE_SELECTOR))
}

function hasScrollableAncestor(target: EventTarget | null) {
  if (!(target instanceof HTMLElement))
    return false

  let element: HTMLElement | null = target
  while (element && element.id !== 'slide-container') {
    const style = window.getComputedStyle(element)
    if (
      /(auto|scroll)/.test(style.overflowY)
      && element.scrollHeight > element.clientHeight + 1
    ) {
      return true
    }
    element = element.parentElement
  }
  return false
}

function onClick(event: MouseEvent) {
  if (
    isPrintMode.value
    || isDrawing.value
    || event.defaultPrevented
    || event.button !== 0
    || event.ctrlKey
    || event.metaKey
    || shouldIgnore(event.target)
    || window.getSelection()?.toString()
  ) {
    return
  }

  if (event.clientX > window.innerWidth / 2)
    next()
  else
    prev()
}

function onWheel(event: WheelEvent) {
  if (
    isPrintMode.value
    || isDrawing.value
    || event.defaultPrevented
    || event.ctrlKey
    || event.shiftKey
    || shouldIgnore(event.target)
    || hasScrollableAncestor(event.target)
    || Math.abs(event.deltaY) < 0.01
  ) {
    return
  }

  event.preventDefault()

  const now = performance.now()
  if (now < wheelLockedUntil) {
    wheelDelta = 0
    return
  }

  if (wheelDelta !== 0 && Math.sign(wheelDelta) !== Math.sign(event.deltaY))
    wheelDelta = 0
  wheelDelta += event.deltaY

  if (Math.abs(wheelDelta) < 24)
    return

  if (wheelDelta > 0)
    next()
  else
    prev()

  wheelDelta = 0
  wheelLockedUntil = now + 450
}

onMounted(() => {
  window.addEventListener('click', onClick)
  window.addEventListener('wheel', onWheel, { passive: false })
})

onBeforeUnmount(() => {
  window.removeEventListener('click', onClick)
  window.removeEventListener('wheel', onWheel)
})
</script>

<template>
  <div class="slidev-pointer-navigation" aria-hidden="true" />
</template>

<style>
.slidev-pointer-navigation {
  display: none;
}
</style>
