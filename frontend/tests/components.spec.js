import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseButton from '../src/components/common/BaseButton.vue'
import StatusBadge from '../src/components/common/StatusBadge.vue'
import KpiCard from '../src/components/common/KpiCard.vue'

describe('BaseButton', () => {
  it('renders its label and emits click', async () => {
    const wrapper = mount(BaseButton, { slots: { default: 'Add to cart' } })
    expect(wrapper.text()).toBe('Add to cart')
    await wrapper.trigger('click')
    expect(wrapper.attributes('disabled')).toBeUndefined()
  })

  it('is disabled and marked busy while loading', () => {
    const wrapper = mount(BaseButton, {
      props: { loading: true },
      slots: { default: 'Placing order' },
    })
    expect(wrapper.attributes('disabled')).toBeDefined()
    expect(wrapper.attributes('aria-busy')).toBe('true')
    expect(wrapper.find('.btn__spinner').exists()).toBe(true)
  })

  it('stays keyboard reachable as a native button', () => {
    const wrapper = mount(BaseButton, { slots: { default: 'Retry' } })
    expect(wrapper.attributes('type')).toBe('button')
  })
})

describe('StatusBadge', () => {
  it('renders the human label with the matching tone', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'SHIPPED' } })
    expect(wrapper.text()).toBe('Shipped')
    expect(wrapper.classes()).toContain('badge--success')
  })

  it('falls back to a neutral tone for unknown statuses', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'WHO_KNOWS' } })
    expect(wrapper.classes()).toContain('badge--neutral')
  })
})

describe('KpiCard', () => {
  it('shows the value and switches to a skeleton while loading', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Total revenue', value: '$7,932.28', caption: 'sum' },
    })
    expect(wrapper.text()).toContain('$7,932.28')
    expect(wrapper.find('.skeleton').exists()).toBe(false)

    const loadingWrapper = mount(KpiCard, {
      props: { label: 'Total revenue', loading: true },
    })
    expect(loadingWrapper.find('.skeleton').exists()).toBe(true)
  })
})
