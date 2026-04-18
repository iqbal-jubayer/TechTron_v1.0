function myFunc(id) {
    window.location.href = `/product/product_no_${id}`;
}

function cancelOrderWarning(){
    let result = confirm("Are you sure you want to cancel this order?");
    if(result == true){
        alert("Order Cancelled!")
    }
}