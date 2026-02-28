# Snake Easter Egg Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a fullscreen Snake game triggered by typing `SNAKE` anywhere on the page (desktop only).

**Architecture:** A single self-contained inline `<script>` block added to `index.html` before `<!-- analytics:start -->`. No build.py changes. The script creates its own overlay + canvas on first trigger, hides/shows on subsequent triggers. One `keydown` listener does double duty: trigger detection when idle, game control when active.

**Tech Stack:** Vanilla JS, HTML5 Canvas, existing CSS tokens (`#050a14`, `#3b82f6`, `#22c55e`, `#f59e0b`).

---

### Task 1: Add the Snake script to index.html

**Files:**
- Modify: `index.html` — insert `<script>` block before `<!-- analytics:start -->` (line ~1361)

No automated tests are possible for a canvas game. Testing is manual (see Step 3).

**Step 1: Insert the script**

Find this line in `index.html` (currently around line 1361):

```html
<!-- analytics:start -->
```

Insert the following `<script>` block immediately before it (no blank line between the boot script and this one):

```html
<script>(function(){if(window.matchMedia('(pointer: coarse)').matches)return;var TRIGGER='SNAKE',buf='',overlay=null,canvas=null,ctx=null,COLS=20,ROWS=20,snake,dir,nextDir,food,score,gameOver,loop,active=false;document.addEventListener('keydown',function(e){if(active){handleGameKey(e);return;}var tag=document.activeElement&&document.activeElement.tagName;if(tag==='INPUT'||tag==='TEXTAREA')return;var ch=e.key.length===1?e.key.toUpperCase():'';if(!ch)return;buf=(buf+ch).slice(-TRIGGER.length);if(buf===TRIGGER){buf='';openGame();}});function openGame(){if(!overlay){overlay=document.createElement('div');overlay.style.cssText='position:fixed;inset:0;z-index:99999;background:#050a14;display:flex;align-items:center;justify-content:center;';canvas=document.createElement('canvas');overlay.appendChild(canvas);document.body.appendChild(overlay);}overlay.style.display='flex';active=true;initGame();}function closeGame(){clearInterval(loop);overlay.style.display='none';active=false;buf='';}function cs(){return Math.floor(Math.min(window.innerWidth,window.innerHeight)*0.9/COLS);}function initGame(){var c=cs();canvas.width=COLS*c;canvas.height=ROWS*c;ctx=canvas.getContext('2d');snake=[{x:10,y:10},{x:9,y:10},{x:8,y:10}];dir={x:1,y:0};nextDir={x:1,y:0};score=0;gameOver=false;placeFood();clearInterval(loop);loop=setInterval(tick,150);draw();}function placeFood(){var empties=[];for(var x=0;x<COLS;x++)for(var y=0;y<ROWS;y++)if(!snake.some(function(s){return s.x===x&&s.y===y;}))empties.push({x:x,y:y});food=empties[Math.floor(Math.random()*empties.length)];}function tick(){dir=nextDir;var h={x:snake[0].x+dir.x,y:snake[0].y+dir.y};if(h.x<0||h.x>=COLS||h.y<0||h.y>=ROWS||snake.some(function(s){return s.x===h.x&&s.y===h.y;})){endGame();return;}snake.unshift(h);if(h.x===food.x&&h.y===food.y){score++;placeFood();clearInterval(loop);loop=setInterval(tick,Math.max(80,150-score*7));}else{snake.pop();}draw();}function draw(){var c=cs();ctx.fillStyle='#050a14';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#22c55e';ctx.fillRect(food.x*c+1,food.y*c+1,c-2,c-2);ctx.fillStyle='#3b82f6';snake.forEach(function(s){ctx.fillRect(s.x*c+1,s.y*c+1,c-2,c-2);});ctx.fillStyle='#94a3b8';ctx.font='bold 14px "JetBrains Mono",monospace';ctx.textAlign='left';ctx.fillText('SCORE: '+score,8,20);}function endGame(){clearInterval(loop);gameOver=true;var cx=canvas.width/2,cy=canvas.height/2;ctx.fillStyle='rgba(5,10,20,0.8)';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.textAlign='center';ctx.fillStyle='#f59e0b';ctx.font='bold 24px "JetBrains Mono",monospace';ctx.fillText('GAME OVER',cx,cy-28);ctx.fillStyle='#e2e8f0';ctx.font='16px "JetBrains Mono",monospace';ctx.fillText('SCORE: '+score,cx,cy+2);ctx.fillStyle='#64748b';ctx.font='13px "JetBrains Mono",monospace';ctx.fillText('[ ESC ] EXIT   [ ENTER ] RESTART',cx,cy+32);}function handleGameKey(e){if(e.key==='Escape'){closeGame();return;}if(gameOver&&e.key==='Enter'){initGame();return;}if(!gameOver){var map={ArrowUp:{x:0,y:-1},ArrowDown:{x:0,y:1},ArrowLeft:{x:-1,y:0},ArrowRight:{x:1,y:0}};var nd=map[e.key];if(nd&&(nd.x!==-dir.x||nd.y!==-dir.y)){nextDir=nd;e.preventDefault();}}}})();</script>
```

**Step 2: Manual test — open index.html in a browser**

Open `index.html` directly in a browser (or run `python3 build.py` first to get a fresh build, then open).

Verify the following:

| Check | Expected |
|-------|----------|
| Page loads normally | Boot sequence runs, site appears as normal |
| Type `SNAKE` (all caps, no form focused) | Fullscreen dark overlay appears with a Snake game |
| Arrow keys move the snake | Snake responds correctly, can't reverse 180° |
| Snake eats food (green square) | Score increments, speed gradually increases |
| Snake hits wall or self | Game-over screen: `GAME OVER` / `SCORE: X` / controls hint |
| Press `ENTER` on game-over | Game restarts cleanly |
| Press `ESC` at any time | Overlay disappears, site is normal |
| Type `SNAKE` again after closing | Game reopens and restarts |
| Type `snake` (lowercase) | Also triggers (case-insensitive via `.toUpperCase()`) |
| Click into a text input, type `SNAKE` | Game does NOT trigger |

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: add Snake easter egg triggered by typing SNAKE"
```

---

### Task 2: Push

```bash
git pull --rebase origin main
git push origin main
```

If rebase conflict on `<!-- updated:start/end -->`: keep OUR `index.html` structure but the bot's timestamp text inside the marker. Then `git add index.html` and `git rebase --continue`.

---

### Task 3: Update roadmap

In `docs/roadmap.md`, mark the Snake item done and update iteration 8 status:

```markdown
- [x] Snake easter egg — triggered by typing `SNAKE` anywhere on page; fullscreen, existing palette; ESC or game-over dismisses
```

Change the iteration 8 heading line from `⬜ planned` to `✅ shipped YYYY-MM-DD`.

Commit:

```bash
git add docs/roadmap.md
git commit -m "docs: mark iteration 8 Snake easter egg complete in roadmap"
git push origin main
```
