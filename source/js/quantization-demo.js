const weights = [-0.82, 0.24, 1.12, -1.57, 0.48, -0.31, 1.86, -0.95, 0.12, -0.69, 0.93, 8.20, -1.24, 0.38, 1.47, -0.53];
    const bitsSelect = document.getElementById('bits');
    const groupSelect = document.getElementById('group');
    const rows = document.getElementById('quantRows');
    const fmt = x => (x >= 0 ? '+' : '') + x.toFixed(2);
    function renderQuantization(){
      const bits = Number(bitsSelect.value), group = Number(groupSelect.value), qmax = 2 ** (bits - 1) - 1;
      const scales = [], reconstructed = [], codes = [];
      for(let i=0;i<weights.length;i+=group){
        const block = weights.slice(i,i+group);
        const scale = Math.max(...block.map(Math.abs))/qmax;
        for(const value of block){
          const code = Math.max(-qmax,Math.min(qmax,Math.round(value/scale)));
          scales.push(scale);codes.push(code);reconstructed.push(code*scale);
        }
      }
      const mse = weights.reduce((sum,w,i)=>sum+(w-reconstructed[i])**2,0)/weights.length;
      document.getElementById('mse').textContent = mse.toFixed(4);
      document.getElementById('effectiveBits').textContent = (bits+16/group).toFixed(2)+' bit/W';
      document.getElementById('outlierScale').textContent = scales[11].toFixed(3);
      rows.replaceChildren();
      weights.forEach((w,i)=>{
        const row=document.createElement('div');row.className='plot-row'+(i===11?' outlier':'');
        const index=document.createElement('span');index.textContent=String(i+1).padStart(2,'0');
        const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 280 25');svg.setAttribute('role','img');svg.setAttribute('aria-label',`原值 ${fmt(w)}，还原 ${fmt(reconstructed[i])}`);
        const axis=document.createElementNS(ns,'line');axis.setAttribute('x1','0');axis.setAttribute('x2','280');axis.setAttribute('y1','13');axis.setAttribute('y2','13');axis.setAttribute('stroke','#d5dcd5');svg.append(axis);
        const zero=document.createElementNS(ns,'line');zero.setAttribute('x1','140');zero.setAttribute('x2','140');zero.setAttribute('y1','2');zero.setAttribute('y2','23');zero.setAttribute('stroke','#abbab3');svg.append(zero);
        const xOf=value=>140+Math.max(-9,Math.min(9,value))*14.7;
        const old=document.createElementNS(ns,'circle');old.setAttribute('cx',xOf(w));old.setAttribute('cy','13');old.setAttribute('r','5');old.setAttribute('fill','#087e79');svg.append(old);
        const newVal=document.createElementNS(ns,'rect');newVal.setAttribute('x',xOf(reconstructed[i])-4);newVal.setAttribute('y','9');newVal.setAttribute('width','8');newVal.setAttribute('height','8');newVal.setAttribute('transform',`rotate(45 ${xOf(reconstructed[i])} 13)`);newVal.setAttribute('fill','#bb5b36');svg.append(newVal);
        const orig=document.createElement('span');orig.textContent=fmt(w);const quant=document.createElement('span');quant.textContent=fmt(reconstructed[i]);const scale=document.createElement('span');scale.className='scale';scale.textContent=scales[i].toFixed(2);
        row.append(index,svg,orig,quant,scale);rows.append(row);
      });
    }
    bitsSelect.addEventListener('change',renderQuantization);groupSelect.addEventListener('change',renderQuantization);renderQuantization();
