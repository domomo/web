import { requestArticlePayment } from './api/portone';

jest.mock('@portone/browser-sdk/v2', () => ({
  requestPayment: jest.fn().mockResolvedValue({ paymentId: 'article-payment-1' }),
}), { virtual: true });

import { requestPayment } from '@portone/browser-sdk/v2';

describe('PortOne V2 article checkout', () => {
  beforeEach(() => jest.clearAllMocks());

  it('uses the server order amount and configured Toss new-module channel', async () => {
    const api = { preparePurchase: jest.fn().mockResolvedValue({
      payment_id: 'article-payment-1', order_name: '유료 글', amount: 3900,
    }) };
    const config = { store_id: 'store-test', channel_key: 'channel-test' };
    const returnUrlForPayment = (paymentId) => `https://example.test/posts/4?paymentId=${paymentId}`;

    await expect(requestArticlePayment(api, 4, config, returnUrlForPayment)).resolves.toBe('article-payment-1');

    expect(requestPayment).toHaveBeenCalledWith({
      storeId: 'store-test',
      channelKey: 'channel-test',
      paymentId: 'article-payment-1',
      orderName: '유료 글',
      totalAmount: 3900,
      currency: 'KRW',
      payMethod: 'CARD',
      redirectUrl: 'https://example.test/posts/4?paymentId=article-payment-1',
    });
  });

  it('rejects a cancelled or failed payment result', async () => {
    const api = { preparePurchase: jest.fn().mockResolvedValue({ payment_id: 'article-payment-1', amount: 3900 }) };
    requestPayment.mockResolvedValueOnce({ code: 'CANCEL', message: '사용자 취소' });

    await expect(requestArticlePayment(api, 4, { store_id: 's', channel_key: 'c' }, () => 'https://example.test'))
      .rejects.toThrow('사용자 취소');
  });
});
