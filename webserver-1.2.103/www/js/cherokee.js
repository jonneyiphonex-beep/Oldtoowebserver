(function () {
    var api = document.querySelector('meta[name="cherokee-monitor-api"]').content;
    var refreshButton = document.getElementById('refresh-button');
    var monitorTitle = document.getElementById('monitor-title');
    var monitorMessage = document.getElementById('monitor-message');
    var monitorDot = document.getElementById('monitor-dot');
    var updatedAt = document.getElementById('updated-at');

    function setText(id, value) {
        document.getElementById(id).textContent = value == null ? 'غير متاح' : String(value);
    }

    function setMetric(name, metric) {
        if (!metric || typeof metric !== 'object') {
            return false;
        }

        var value = document.getElementById(name + '-value');
        var detail = document.getElementById(name + '-detail');

        if (name === 'ram' || name === 'disk') {
            if (metric.used_percent == null || metric.used_percent === '') {
                return false;
            }
            var percent = Number(metric.used_percent);
            if (!Number.isFinite(percent)) {
                return false;
            }

            percent = Math.max(0, Math.min(100, percent));
            value.textContent = Math.round(percent) + '%';
            var meter = document.getElementById(name + '-meter');
            meter.style.width = percent + '%';
            meter.parentElement.setAttribute('aria-valuenow', String(Math.round(percent)));
            detail.textContent = metric.used_text && metric.total_text
                ? metric.used_text + ' مستخدم من ' + metric.total_text
                : 'لا تتوفر تفاصيل السعة';
            return true;
        }

        if (name === 'internet' || name === 'ethernet') {
            if (metric.status !== 'online' && metric.status !== 'offline' && metric.status !== 'unknown') {
                return false;
            }
            value.textContent = metric.status === 'online' ? 'متصل'
                : metric.status === 'offline' ? 'غير متصل' : 'غير معروف';
        } else if (name === 'ports') {
            if (metric.count == null || !Number.isFinite(Number(metric.count)) || Number(metric.count) < 0) {
                return false;
            }
            value.textContent = String(metric.count);
        } else if (name === 'backdoor') {
            if (metric.status !== 'clear' && metric.status !== 'warning' && metric.status !== 'unknown') {
                return false;
            }
            value.textContent = metric.status === 'clear' ? 'لا مؤشرات مرصودة'
                : metric.status === 'warning' ? 'يتطلب المراجعة' : 'غير معروف';
        }

        detail.textContent = metric.detail || 'لا توجد تفاصيل إضافية';
        return true;
    }

    function showUnavailable(message) {
        monitorTitle.textContent = 'واجهة المراقبة غير متاحة';
        monitorMessage.textContent = message;
        monitorDot.classList.add('is-offline');
        ['ram', 'disk', 'internet', 'ethernet', 'ports', 'backdoor'].forEach(function (name) {
            setText(name + '-value', 'غير متاح');
            setText(name + '-detail', 'لا توجد بيانات موثوقة');
        });
    }

    function refreshMetrics() {
        if (refreshButton.disabled) {
            return;
        }
        refreshButton.disabled = true;
        monitorTitle.textContent = 'جارٍ جلب القياسات';
        monitorMessage.textContent = 'الاتصال بخدمة المراقبة الآمنة...';

        window.fetch(api, { cache: 'no-store', credentials: 'same-origin' })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(function (data) {
                var validMetrics = ['ram', 'disk', 'internet', 'ethernet', 'ports', 'backdoor'].reduce(function (count, name) {
                    return count + (setMetric(name, data[name]) ? 1 : 0);
                }, 0);

                if (!validMetrics) {
                    throw new Error('No valid metrics');
                }
                monitorTitle.textContent = 'تم تحديث القياسات';
                monitorMessage.textContent = 'تم استلام ' + validMetrics + ' من 6 مؤشرات.';
                monitorDot.classList.remove('is-offline', 'is-warning');
                updatedAt.textContent = new Date().toLocaleTimeString('ar');
            })
            .catch(function () {
                showUnavailable('تعذر الاتصال بواجهة القياس. لا تعرض الصفحة بيانات افتراضية.');
                updatedAt.textContent = new Date().toLocaleTimeString('ar') + ' (فشل الاتصال)';
            })
            .then(function () {
                refreshButton.disabled = false;
            });
    }

    refreshButton.addEventListener('click', refreshMetrics);
    refreshMetrics();
    window.setInterval(refreshMetrics, 15000);
}());