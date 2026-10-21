export async function requestArticlePayment(api, boardIdx, config, returnUrlForPayment) {
  const order = await api.preparePurchase(boardIdx);
  const PortOne = await import('@portone/browser-sdk/v2');
  const result = await PortOne.requestPayment({
    storeId: config.store_id,
    channelKey: config.channel_key,
    paymentId: order.payment_id,
    orderName: order.order_name,
    totalAmount: order.amount,
    currency: 'KRW',
    payMethod: 'CARD',
    redirectUrl: returnUrlForPayment(order.payment_id),
  });
  if (result?.code) throw new Error(result.message || '결제가 취소되었거나 실패했어요.');
  if (!result?.paymentId) throw new Error('결제 결과를 확인하지 못했어요.');
  return result.paymentId;
}
