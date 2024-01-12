function pay() {
    if (confirm("Bạn chắc chắn thanh toán không?") == true) {
        fetch("/api/pay").then(res => res.json()).then(data => {
            if (data.status === 200)
                location.reload()
            else
                alert("Hệ thống đang bị lỗi!")
        })
    }
}

function sendOtp() {
    fetch("/sendotp", {
        method: "send"
    }).then(() => alert("Mã OTP đã được gửi vào mail của bạn"))
}