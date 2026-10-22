import { onMounted } from 'vue'
import { onSlideEnter, useSlideContext } from '@slidev/client'

/**
 * One lifecycle for every animation of the deck.
 *
 * - Live contexts (the slide itself, the presenter's current slide): `setup` puts the element in its start state
 *   when it is created (slides are created before they are shown), and `enter` plays the animation each time the
 *   slide becomes the current one, and only then. Nothing is reset on leave, so the outgoing slide keeps its final
 *   state while the slide transition runs.
 * - Static contexts (the presenter's "next slide" preview, the overview, PDF export, reduced motion): `final`
 *   shows the end state at once and nothing ever animates.
 */
export function isStaticContext(context: string): boolean {
  if (typeof window === 'undefined') return true
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return true
  if (window.location.search.includes('print') || window.location.pathname.includes('/export')) return true
  return context !== 'slide' && context !== 'presenter'
}

export function useStage(handlers: { setup?: () => void, enter: () => void, final: () => void }) {
  const { $renderContext } = useSlideContext()
  const still = () => isStaticContext($renderContext.value)
  onMounted(() => {
    if (still()) handlers.final()
    else handlers.setup?.()
  })
  onSlideEnter(() => {
    if (!still()) handlers.enter()
  })
  return { still }
}
