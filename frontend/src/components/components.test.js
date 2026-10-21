import { mount } from '@vue/test-utils';
import AccountPanel from './AccountPanel.vue';
import BrandButton from './BrandButton.vue';
import ProductDetail from './ProductDetail.vue';
import ServiceCard from './ServiceCard.vue';
import ServiceHeader from './ServiceHeader.vue';
import ServiceTabs from './ServiceTabs.vue';

describe('reusable service components', () => {
  it('switches service tabs and emits the selected value', async () => {
    const wrapper = mount(ServiceTabs, {
      props: {
        tabs: [{ label: '개인', value: 'service' }, { label: '비즈니스', value: 'business' }],
        modelValue: 'service',
      },
    });

    await wrapper.get('[role="tab"]:nth-child(2)').trigger('click');

    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['business']);
    expect(wrapper.emitted('change')[0]).toEqual(['business']);
  });

  it('supports keyboard navigation between service tabs', async () => {
    const wrapper = mount(ServiceTabs, {
      props: {
        tabs: [{ label: '개인', value: 'service' }, { label: '비즈니스', value: 'business' }],
        modelValue: 'service',
      },
    });
    const nextTab = wrapper.get('[role="tab"]:nth-child(2)').element;
    const focus = jest.spyOn(nextTab, 'focus');

    await wrapper.get('[role="tab"]').trigger('keydown', { key: 'ArrowRight' });

    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['business']);
    expect(focus).toHaveBeenCalled();
  });

  it('makes disabled action links unavailable', () => {
    const wrapper = mount(BrandButton, { props: { href: '/start', disabled: true }, slots: { default: '시작하기' } });
    expect(wrapper.get('a').attributes('href')).toBeUndefined();
    expect(wrapper.get('a').attributes('aria-disabled')).toBe('true');
  });

  it('renders a reusable service card with its call to action', () => {
    const wrapper = mount(ServiceCard, {
      props: { title: '간편 결제', description: '빠르고 안전한 결제', href: '/payments' },
    });

    expect(wrapper.text()).toContain('간편 결제');
    expect(wrapper.get('a').attributes('href')).toBe('/payments');
  });

  it('renders product features and emits its primary action', async () => {
    const wrapper = mount(ProductDetail, {
      props: { title: '상품 소개', description: '상품 설명', features: ['빠른 시작'] },
    });

    expect(wrapper.text()).toContain('빠른 시작');
    await wrapper.get('button').trigger('click');
    expect(wrapper.emitted('action')).toHaveLength(1);
  });

  it('submits login values and provides signup fields in signup mode', async () => {
    const login = mount(AccountPanel, { props: { mode: 'login' } });
    await login.get('input[name="email"]').setValue('person@example.com');
    await login.get('input[name="password"]').setValue('secret123');
    await login.get('form').trigger('submit');
    expect(login.emitted('submit')[0][0]).toMatchObject({ email: 'person@example.com', password: 'secret123' });

    const signup = mount(AccountPanel, { props: { mode: 'signup' } });
    expect(signup.find('input[name="name"]').exists()).toBe(true);
  });

  it('shows service and business navigation with account actions', () => {
    const wrapper = mount(ServiceHeader, {
      props: {
        navItems: [{ label: '서비스', to: '/posts' }, { label: '비즈니스', to: '/posts?view=business' }],
        loginTo: '/login',
        signupTo: '/signup',
      },
      global: { stubs: { RouterLink: { props: ['to'], template: '<a><slot /></a>' } } },
    });
    expect(wrapper.text()).toContain('서비스');
    expect(wrapper.text()).toContain('비즈니스');
    expect(wrapper.text()).toContain('회원가입');
  });

  it('shows the signed-in user profile in place of login actions', () => {
    const wrapper = mount(ServiceHeader, {
      props: {
        navItems: [{ label: '서비스', to: '/posts' }],
        loginTo: '/login',
        signupTo: '/signup',
        user: { name: '지민', email: 'jimin@example.com' },
      },
      global: { stubs: { RouterLink: { props: ['to'], template: '<a><slot /></a>' } } },
    });

    expect(wrapper.get('[data-testid="user-profile"]').text()).toContain('지민님');
    expect(wrapper.text()).not.toContain('로그인');
    expect(wrapper.text()).not.toContain('회원가입');
  });
});
