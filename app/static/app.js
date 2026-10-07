const { createApp, ref, reactive, computed, watch, onMounted, nextTick } = Vue;
const PALETTE = ['#e4572e','#29335c','#f3a712','#4ea8de','#6a994e','#a8dadc','#9b5de5','#f15bb5'];

createApp({
  setup() {
    const meta = ref(null), data = ref(null), loading = ref(false), error = ref('');
    const refs = { trend: ref(null), outlet: ref(null), type: ref(null), group: ref(null),
                   hour: ref(null), items: ref(null), settle: ref(null) };
    const charts = {};
    const f = reactive({ start: '', end: '', outlet: [], group: [], order_type: [], settlement: [], grain: 'month' });
    const dims = [
      { key: 'outlet', label: 'Outlet', opts: 'outlets' },
      { key: 'group', label: 'Category', opts: 'groups' },
      { key: 'order_type', label: 'Order type', opts: 'order_types' },
      { key: 'settlement', label: 'Payment', opts: 'settlements' },
    ];

    const qs = () => {
      const p = new URLSearchParams();
      if (f.start) p.set('start', f.start);
      if (f.end) p.set('end', f.end);
      ['outlet', 'group', 'order_type', 'settlement'].forEach(k => f[k].forEach(v => p.append(k, v)));
      return p;
    };
    const exportUrl = computed(() => '/api/export.csv?' + qs().toString());
    const n = v => Number(v).toLocaleString('en-IN');

    function draw(key, cfg) {
      const el = refs[key].value; if (!el) return;
      if (charts[key]) charts[key].destroy();
      charts[key] = new Chart(el, cfg);
    }
    const base = { responsive: true, maintainAspectRatio: false, animation: { duration: 250 } };
    const money = v => '₹' + Number(v).toLocaleString('en-IN');

    function render(d) {
      draw('trend', { type: 'line', data: { labels: d.trend.map(t => t.x),
        datasets: [{ label: 'Revenue', data: d.trend.map(t => t.revenue), borderColor: PALETTE[0],
          backgroundColor: PALETTE[0] + '22', fill: true, tension: .3, pointRadius: d.trend.length > 60 ? 0 : 3 }] },
        options: { ...base, plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: money } } } } });
      draw('outlet', { type: 'bar', data: { labels: d.by_outlet.map(o => o.label),
        datasets: [{ data: d.by_outlet.map(o => o.revenue), backgroundColor: PALETTE[1] }] },
        options: { ...base, plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: money } } } } });
      const pie = (arr) => ({ type: 'doughnut', data: { labels: arr.map(a => a.label),
        datasets: [{ data: arr.map(a => a.revenue), backgroundColor: PALETTE }] },
        options: { ...base, plugins: { legend: { position: 'bottom' } } } });
      draw('type', pie(d.by_type));
      draw('settle', pie(d.by_settlement));
      draw('group', { type: 'bar', data: { labels: d.by_group.map(g => g.label),
        datasets: [{ data: d.by_group.map(g => g.revenue), backgroundColor: PALETTE[2] }] },
        options: { ...base, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { ticks: { callback: money } } } } });
      draw('hour', { type: 'bar', data: { labels: d.hourly.map(h => h.label),
        datasets: [{ data: d.hourly.map(h => h.orders), backgroundColor: PALETTE[3] }] },
        options: { ...base, plugins: { legend: { display: false } } } });
      draw('items', { type: 'bar', data: { labels: d.top_items.map(i => i.label),
        datasets: [{ data: d.top_items.map(i => i.revenue), backgroundColor: PALETTE[4] }] },
        options: { ...base, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { ticks: { callback: money } } } } });
    }

    let seq = 0, timer;
    async function load() {
      const my = ++seq; loading.value = true; error.value = '';
      const p = qs(); p.set('grain', f.grain);
      try {
        const r = await fetch('/api/dashboard?' + p.toString());
        if (!r.ok) throw new Error('API ' + r.status);
        const j = await r.json();
        if (my !== seq) return;                 // ignore stale responses
        data.value = j; await nextTick(); render(j);
      } catch (e) { error.value = 'Failed to load data: ' + e.message; }
      finally { if (my === seq) loading.value = false; }
    }
    const toggle = (k, v) => { const a = f[k], i = a.indexOf(v); i < 0 ? a.push(v) : a.splice(i, 1); };
    const reset = () => { f.start = meta.value.min_date; f.end = meta.value.max_date;
      f.outlet = []; f.group = []; f.order_type = []; f.settlement = []; f.grain = 'month'; };

    watch(f, () => { clearTimeout(timer); timer = setTimeout(load, 200); }, { deep: true }); // debounce

    onMounted(async () => {
      try {
        meta.value = await (await fetch('/api/meta')).json();
        f.start = meta.value.min_date; f.end = meta.value.max_date;   // triggers first load via watcher
      } catch (e) { error.value = 'Failed to reach API'; }
    });

    return { meta, data, loading, error, f, dims, toggle, reset, exportUrl, n, ...refs };
  }
}).mount('#app');