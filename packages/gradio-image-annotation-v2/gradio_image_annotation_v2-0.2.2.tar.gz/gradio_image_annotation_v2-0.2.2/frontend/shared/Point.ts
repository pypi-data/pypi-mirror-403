import WindowViewer from "./WindowViewer";

const clamp = (num: number, min: number, max: number) =>
  Math.min(Math.max(num, min), max);

function setAlpha(rgbColor: string, alpha: number) {
  if (rgbColor.startsWith("rgba")) {
    return rgbColor.replace(/[\d.]+$/, alpha.toString());
  }
  const matches = rgbColor.match(/\d+/g);
  if (!matches || matches.length !== 3) {
    return `rgba(50, 50, 50, ${alpha})`;
  }
  const [r, g, b] = matches;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export default class Point {
  label: string;
  x: number;
  y: number;
  _x: number;
  _y: number;
  color: string;
  alpha: number;
  radius: number;
  isDragging: boolean;
  isSelected: boolean;
  offsetMouseX: number;
  offsetMouseY: number;
  renderCallBack: () => void;
  canvasXmin: number;
  canvasYmin: number;
  canvasXmax: number;
  canvasYmax: number;
  scaleFactor: number;
  canvasWindow: WindowViewer;
  pointersCache: Map<number, PointerEvent>;

  constructor(
    renderCallBack: () => void,
    canvasWindow: WindowViewer,
    pointersCache: Map<number, PointerEvent>,
    canvasXmin: number,
    canvasYmin: number,
    canvasXmax: number,
    canvasYmax: number,
    label: string,
    x: number,
    y: number,
    color = "rgb(255, 255, 255)",
    alpha = 0.6,
    radius = 6,
    scaleFactor = 1
  ) {
    this.renderCallBack = renderCallBack;
    this.canvasWindow = canvasWindow;
    this.pointersCache = pointersCache;
    this.canvasXmin = canvasXmin;
    this.canvasYmin = canvasYmin;
    this.canvasXmax = canvasXmax;
    this.canvasYmax = canvasYmax;
    this.scaleFactor = scaleFactor;
    this.label = label;
    this.isDragging = false;
    this.isSelected = false;
    this._x = x;
    this._y = y;
    this.x = this._x * this.canvasWindow.scale;
    this.y = this._y * this.canvasWindow.scale;
    this.color = color;
    this.alpha = alpha;
    this.radius = radius;
    this.offsetMouseX = 0;
    this.offsetMouseY = 0;
  }

  toJSON() {
    return {
      label: this.label,
      x: this._x,
      y: this._y,
      color: this.color,
      scaleFactor: this.scaleFactor,
    };
  }

  setSelected(selected: boolean) {
    this.isSelected = selected;
  }

  setScaleFactor(scaleFactor: number) {
    const scale = scaleFactor / this.scaleFactor;
    this._x = Math.round(this._x * scale);
    this._y = Math.round(this._y * scale);
    this.applyUserScale();
    this.scaleFactor = scaleFactor;
  }

  applyUserScale() {
    this.x = this._x * this.canvasWindow.scale;
    this.y = this._y * this.canvasWindow.scale;
  }

  updateOffset() {
    this.canvasXmin = this.canvasWindow.offsetX;
    this.canvasYmin = this.canvasWindow.offsetY;
    this.canvasXmax =
      this.canvasWindow.offsetX +
      this.canvasWindow.imageWidth * this.canvasWindow.scale;
    this.canvasYmax =
      this.canvasWindow.offsetY +
      this.canvasWindow.imageHeight * this.canvasWindow.scale;
    this.applyUserScale();
  }

  toCanvasCoordinates(x: number, y: number): [number, number] {
    x = x + this.canvasXmin;
    y = y + this.canvasYmin;
    return [x, y];
  }

  toPointCoordinates(x: number, y: number): [number, number] {
    x = x - this.canvasXmin;
    y = y - this.canvasYmin;
    return [x, y];
  }

  isPointInsidePoint(x: number, y: number): boolean {
    [x, y] = this.toPointCoordinates(x, y);
    const radius = this.radius * (this.isSelected ? 1.4 : 1);
    const dx = x - this.x;
    const dy = y - this.y;
    return dx * dx + dy * dy <= radius * radius;
  }

  render(ctx: CanvasRenderingContext2D) {
    this.updateOffset();
    const [cx, cy] = this.toCanvasCoordinates(this.x, this.y);
    const radius = this.radius * (this.isSelected ? 1.4 : 1);

    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fillStyle = setAlpha(this.color, this.alpha);
    ctx.fill();
    ctx.lineWidth = this.isSelected ? 2 : 1;
    ctx.strokeStyle = setAlpha(this.color, 1);
    ctx.stroke();
    ctx.closePath();

    if (this.label !== null && this.label.trim() !== "") {
      ctx.font = this.isSelected ? "bold 14px Arial" : "12px Arial";
      const labelWidth = ctx.measureText(this.label).width + 10;
      const labelHeight = 20;
      const labelX = cx - labelWidth / 2;
      const labelY = cy - radius - labelHeight - 4;
      ctx.fillStyle = "white";
      ctx.fillRect(labelX, labelY, labelWidth, labelHeight);
      ctx.lineWidth = 1;
      ctx.strokeStyle = "black";
      ctx.strokeRect(labelX, labelY, labelWidth, labelHeight);
      ctx.fillStyle = "black";
      ctx.fillText(this.label, labelX + 5, labelY + 15);
    }
  }

  startDrag(event: MouseEvent) {
    this.isDragging = true;
    this.offsetMouseX = event.clientX - this._x * this.canvasWindow.scale;
    this.offsetMouseY = event.clientY - this._y * this.canvasWindow.scale;
    document.addEventListener("pointermove", this.handleDrag);
    document.addEventListener("pointerup", this.stopDrag);
  }

  stopDrag = () => {
    this.isDragging = false;
    document.removeEventListener("pointermove", this.handleDrag);
    document.removeEventListener("pointerup", this.stopDrag);
  };

  handleDrag = (event: MouseEvent) => {
    if (this.isDragging && this.pointersCache.size === 1) {
      let deltaX =
        (event.clientX - this.offsetMouseX) / this.canvasWindow.scale - this._x;
      let deltaY =
        (event.clientY - this.offsetMouseY) / this.canvasWindow.scale - this._y;

      const canvasW = (this.canvasXmax - this.canvasXmin) / this.canvasWindow.scale;
      const canvasH = (this.canvasYmax - this.canvasYmin) / this.canvasWindow.scale;
      const minPadding = this.radius / this.canvasWindow.scale;
      deltaX = clamp(deltaX, -this._x + minPadding, canvasW - this._x - minPadding);
      deltaY = clamp(deltaY, -this._y + minPadding, canvasH - this._y - minPadding);
      this._x += deltaX;
      this._y += deltaY;
      this.applyUserScale();
      this.renderCallBack();
    }
  };

  onRotate(op: number) {
    const [_x, _y] = [this._x, this._y];
    switch (op) {
      case 1:
        this._x = this.canvasWindow.imageWidth - _y;
        this._y = _x;
        break;
      case -1:
        this._x = _y;
        this._y = this.canvasWindow.imageHeight - _x;
        break;
    }
    this.applyUserScale();
  }
}
