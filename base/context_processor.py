from store.utils import cookieCart, cartData, guestOrder


def default(request):
        data = cartData(request)
        cartItems = data['cartItems']
        
        return{'data': data,
               'cartItems': cartItems}