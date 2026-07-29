/**
 * Dialog keyboard behaviour shared by the detail modals.
 *
 * Each modal is a Teleported overlay with no focus management of its own, so
 * without this a keyboard user can Tab straight out of the dialog into the page
 * behind it and has no way to dismiss it (WCAG 2.1.1, 2.4.3).
 *
 * The listener is on `document` rather than the overlay element because the
 * overlay is a plain div: it never receives key events unless something inside
 * it happens to be focused.
 */
import { watch, nextTick, onBeforeUnmount } from 'vue'

const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])'
].join(', ')

// offsetParent is null for display:none subtrees, which keeps hidden controls
// out of the tab cycle
const visibleFocusable = (container) =>
  Array.from(container.querySelectorAll(FOCUSABLE_SELECTOR)).filter(
    (element) => element.offsetParent !== null
  )

/**
 * @param {() => boolean} isOpen      Getter for the modal's open state.
 * @param {import('vue').Ref<HTMLElement|null>} containerRef  The dialog element.
 * @param {() => void} close          Called when the user presses Escape.
 */
export function useModalA11y(isOpen, containerRef, close) {
  let previouslyFocused = null

  const onKeydown = (event) => {
    if (event.key === 'Escape') {
      close()
      return
    }

    if (event.key !== 'Tab' || !containerRef.value) return

    const focusable = visibleFocusable(containerRef.value)
    if (focusable.length === 0) return

    const first = focusable[0]
    const last = focusable[focusable.length - 1]

    // Wrap at both ends so focus cannot leave the dialog
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  const stopListening = () => document.removeEventListener('keydown', onKeydown)

  watch(isOpen, async (open) => {
    if (open) {
      previouslyFocused = document.activeElement
      document.addEventListener('keydown', onKeydown)

      // Wait for the Transition to put the dialog in the DOM before focusing it
      await nextTick()
      if (!containerRef.value) return
      const [firstFocusable] = visibleFocusable(containerRef.value)
      ;(firstFocusable || containerRef.value).focus()
    } else {
      stopListening()
      // Return the user to whatever opened the dialog, not the top of the page
      if (previouslyFocused instanceof HTMLElement) previouslyFocused.focus()
      previouslyFocused = null
    }
  })

  onBeforeUnmount(stopListening)
}
