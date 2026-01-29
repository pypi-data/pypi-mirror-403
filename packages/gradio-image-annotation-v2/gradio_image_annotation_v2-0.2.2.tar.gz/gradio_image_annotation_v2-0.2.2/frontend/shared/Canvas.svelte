<script lang="ts">
	import { onMount, createEventDispatcher } from "svelte";
	import {
		BoundingBox,
		Point,
		Hand,
		Trash,
		Label,
		Clear,
	} from "./icons/index";
	import ModalBox from "./ModalBox.svelte";
	import Box from "./Box";
	import PointShape from "./Point";
	import { Colors } from "./Colors.js";
	import AnnotatedImageData from "./AnnotatedImageData";
	import { Undo, Redo } from "@gradio/icons";
	import WindowViewer from "./WindowViewer";

	enum Mode {
		creation,
		point,
		drag,
	}

	export let imageUrl: string | null = null;
	export let interactive: boolean;
	export let boxAlpha = 0.5;
	export let handleSize: number;
	export let boxThickness: number;
	export let boxSelectedThickness: number;
	export let value: null | AnnotatedImageData;
	export let choices = [];
	export let choicesColors = [];
	export let disableEditBoxes: boolean = false;
	export let height: number | string = "100%";
	export let width: number | string = "100%";
	export let singleBox: boolean = false;
	export let showRemoveButton: boolean = null;
	export let handlesCursor: boolean | null = true;
	export let useDefaultLabel: boolean = false;
	export let enableKeyboardShortcuts: boolean = true;
	export let selectedAnnotationId: string | null = null;
	export let focusSelectedOnly: boolean = false;
	export let onClearSelection: (() => void) | null = null;

	if (showRemoveButton === null) {
		showRemoveButton = disableEditBoxes;
	}

	// NOTE:
	// `handlesCursor` は外部から渡される可能性がある props ですが、
	// このコンポーネント内で参照しないと「unused export property」警告になります。
	// ここで参照だけして警告を抑止します（挙動は変えません）。
	$: handlesCursor;

	let canvas: HTMLCanvasElement;
	let annotatorContainerDiv: HTMLDivElement;
	let ctx: CanvasRenderingContext2D;
	let image = null;
	let selectedBox = -1;
	let selectedPoint = -1;
	let selectedTarget: "box" | "point" | null = null;
	let mode: Mode = Mode.creation;
	let isMouseDragging = false;
	let isMouseResizing = false;
	let activeResizeCursor: string | null = null;
	let pointersCache: Map<number, PointerEvent> = new Map();
	let canvasWindow: WindowViewer = new WindowViewer(draw, pointersCache);

	function setCursorBasedOnMode() {
		if (!canvas) return;
		if (mode === Mode.creation || mode === Mode.point) {
			canvas.style.cursor = "crosshair";
		} else {
			canvas.style.cursor = "default";
		}
	}

	function startMouseDragCursor() {
		if (!canvas) return;
		isMouseDragging = true;
		canvas.style.cursor = "grabbing";
	}

	function startMouseResizeCursor(cursor: string) {
		if (!canvas) return;
		isMouseResizing = true;
		activeResizeCursor = cursor;
		canvas.style.cursor = cursor;
	}

	function stopMouseDragCursor() {
		if (!canvas) return;
		isMouseDragging = false;
		setCursorBasedOnMode();
	}

	function stopMouseResizeCursor() {
		if (!canvas) return;
		isMouseResizing = false;
		activeResizeCursor = null;
		setCursorBasedOnMode();
	}

	$: if (canvas) {
		// マウス押下中のカーソルを優先
		// - リサイズ中: ハンドル方向の矢印カーソルを固定
		// - ドラッグ/パン中: grabbing
		if (isMouseResizing) {
			canvas.style.cursor = activeResizeCursor ?? "default";
		} else if (isMouseDragging) {
			canvas.style.cursor = "grabbing";
		} else {
			setCursorBasedOnMode();
		}
	}

	if (value !== null && value.boxes.length == 0 && value.points.length == 0) {
		mode = Mode.creation;
	}

	let canvasXmin = 0;
	let canvasYmin = 0;
	let canvasXmax = 0;
	let canvasYmax = 0;
	let scaleFactor = 1.0;

	let imageWidth = 0;
	let imageHeight = 0;

	let editModalVisible = false;
	let newModalVisible = false;
	let editDefaultLabelVisible = false;
	let pointCreationPending = false;

	let labelDetailLock = useDefaultLabel;
	let defaultLabelCache = {
		label: "",
		color: "",
	};
	let selectedLabel = "";
	let selectedColor = "";
	$: {
		if (selectedTarget === "box" && selectedBox >= 0) {
			selectedLabel = value.boxes[selectedBox]?.label ?? "";
			selectedColor = value.boxes[selectedBox]
				? colorRGBAToHex(value.boxes[selectedBox].color)
				: "";
		} else if (selectedTarget === "point" && selectedPoint >= 0) {
			selectedLabel = value.points[selectedPoint]?.label ?? "";
			selectedColor = value.points[selectedPoint]
				? colorRGBAToHex(value.points[selectedPoint].color)
				: "";
		} else {
			selectedLabel = "";
			selectedColor = "";
		}
	}

	let touchScaleValues = {
		x: 0,
		y: 0,
		distance: 0,
	};
	const touchScaleDeadzone = 100;
	let selectedInfo: { type: "box" | "point"; index: number } | null = null;
	let lastSelectedAnnotationId: string | null = null;

	function parseSelectedAnnotationId(
		id: string | null,
		data: AnnotatedImageData,
	) {
		if (!id) {
			return null;
		}
		const [typeValue, indexValue] = id.split("-");
		const index = Number(indexValue);
		if (!Number.isInteger(index) || index < 0) {
			return null;
		}
		if (typeValue === "box") {
			return index < data.boxes.length
				? { type: "box" as const, index }
				: null;
		}
		if (typeValue === "point") {
			return index < data.points.length
				? { type: "point" as const, index }
				: null;
		}
		return null;
	}

	function getVisibleBoxEntries() {
		if (!value) {
			return [] as { box: Box; index: number }[];
		}
		if (focusSelectedOnly) {
			if (selectedInfo?.type === "box") {
				const box = value.boxes[selectedInfo.index];
				return box ? [{ box, index: selectedInfo.index }] : [];
			}
			return [];
		}
		return value.boxes.map((box, index) => ({ box, index }));
	}

	function getVisiblePointEntries() {
		if (!value) {
			return [] as { point: PointShape; index: number }[];
		}
		if (focusSelectedOnly) {
			if (selectedInfo?.type === "point") {
				const point = value.points[selectedInfo.index];
				return point ? [{ point, index: selectedInfo.index }] : [];
			}
			return [];
		}
		return value.points.map((point, index) => ({ point, index }));
	}

	$: {
		if (!value) {
			selectedInfo = null;
			lastSelectedAnnotationId = null;
		} else {
			selectedInfo = parseSelectedAnnotationId(
				selectedAnnotationId,
				value,
			);
			const selectionChanged =
				selectedAnnotationId !== lastSelectedAnnotationId;
			if (selectedInfo) {
				if (selectedInfo.type === "box") {
					if (
						selectedTarget !== "box" ||
						selectedBox !== selectedInfo.index
					) {
						selectBox(selectedInfo.index);
					}
				} else if (
					selectedTarget !== "point" ||
					selectedPoint !== selectedInfo.index
				) {
					selectPoint(selectedInfo.index);
				}
				if (selectionChanged && mode !== Mode.drag) {
					setDragMode();
				}
			}
			lastSelectedAnnotationId = selectedAnnotationId;
		}
	}

	const dispatch = createEventDispatcher<{
		change: undefined;
	}>();

	function colorHexToRGB(hex: string) {
		var r = parseInt(hex.slice(1, 3), 16),
			g = parseInt(hex.slice(3, 5), 16),
			b = parseInt(hex.slice(5, 7), 16);
		return "rgb(" + r + ", " + g + ", " + b + ")";
	}

	function colorRGBAToHex(rgba: string) {
		const rgbaValues = rgba.match(/(\d+(\.\d+)?)/g);
		const r = parseInt(rgbaValues[0]);
		const g = parseInt(rgbaValues[1]);
		const b = parseInt(rgbaValues[2]);
		const hex =
			"#" + ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1);
		return hex;
	}

	function draw() {
		if (ctx) {
			ctx.clearRect(0, 0, canvas.width, canvas.height);
			ctx.save();
			ctx.translate(canvasWindow.offsetX, canvasWindow.offsetY);
			ctx.scale(canvasWindow.scale, canvasWindow.scale);
			if (image !== null) {
				switch (value.orientation) {
					case 0:
						ctx.drawImage(image, 0, 0, imageWidth, imageHeight);
						break;
					case 1:
						ctx.translate(imageWidth, 0);
						ctx.rotate(Math.PI / 2);
						ctx.drawImage(image, 0, 0, imageHeight, imageWidth);
						break;
					case 2:
						ctx.translate(imageWidth, imageHeight);
						ctx.rotate(Math.PI);
						ctx.drawImage(image, 0, 0, imageWidth, imageHeight);
						break;
					case 3:
						ctx.translate(0, imageHeight);
						ctx.rotate(-Math.PI / 2);
						ctx.drawImage(image, 0, 0, imageHeight, imageWidth);
						break;
				}

				ctx.restore();
			}

			const visibleBoxes = getVisibleBoxEntries().slice().reverse();
			for (const { box } of visibleBoxes) {
				box.render(ctx);
			}

			const visiblePoints = getVisiblePointEntries().slice().reverse();
			for (const { point } of visiblePoints) {
				point.render(ctx);
			}
		}
	}

	function drawAndNotify() {
		draw();
		dispatch("change");
	}

	function selectBox(index: number) {
		selectedTarget = index >= 0 ? "box" : null;
		selectedBox = index;
		selectedPoint = -1;
		value.boxes.forEach((box) => {
			box.setSelected(false);
		});
		value.points.forEach((point) => {
			point.setSelected(false);
		});
		if (index >= 0 && index < value.boxes.length) {
			value.boxes[index].setSelected(true);
		}
		draw();
	}

	function selectPoint(index: number) {
		selectedTarget = index >= 0 ? "point" : null;
		selectedPoint = index;
		selectedBox = -1;
		value.boxes.forEach((box) => {
			box.setSelected(false);
		});
		value.points.forEach((point) => {
			point.setSelected(false);
		});
		if (index >= 0 && index < value.points.length) {
			value.points[index].setSelected(true);
		}
		draw();
	}

	const getDistance = (touch1: PointerEvent, touch2: PointerEvent) => {
		const distance = Math.sqrt(
			Math.pow(touch1.clientX - touch2.clientX, 2) +
				Math.pow(touch1.clientY - touch2.clientY, 2),
		);
		return distance < touchScaleDeadzone ? touchScaleDeadzone : distance;
	};

	function handlePointerDown(event: PointerEvent) {
		if (!interactive) {
			return;
		}

		event.preventDefault();
		canvas.setPointerCapture(event.pointerId);
		pointersCache.set(event.pointerId, event);

		if (pointersCache.size == 1) {
			if (mode === Mode.creation) {
				createBox(event);
			} else if (mode === Mode.point) {
				createPoint(event);
			} else if (mode === Mode.drag) {
				clickSelection(event);
			}
		} else if (pointersCache.size == 2) {
			canvasWindow.isDragging = false;
			value.boxes.forEach((box) => {
				box.isCreating = false;
				box.isDragging = false;
				box.isResizing = false;
			});
			value.points.forEach((point) => {
				point.isDragging = false;
			});
			const pointerArray = Array.from(pointersCache.values());
			const touch1 = pointerArray[0];
			const touch2 = pointerArray[1];
			const distance = getDistance(touch1, touch2);
			const rect = canvas.getBoundingClientRect();
			const centerX = (touch1.clientX + touch2.clientX) / 2 - rect.left;
			const centerY = (touch1.clientY + touch2.clientY) / 2 - rect.top;

			touchScaleValues.distance = distance;
			touchScaleValues.x = centerX;
			touchScaleValues.y = centerY;
		}
	}

	function clickBox(event: PointerEvent): boolean {
		const rect = canvas.getBoundingClientRect();
		const mouseX = event.clientX - rect.left;
		const mouseY = event.clientY - rect.top;
		let selectedBoxFlag = false;

		// Check if the mouse is over any of the resizing handles
		for (const { box, index } of getVisibleBoxEntries()) {
			const handleIndex = box.indexOfPointInsideHandle(mouseX, mouseY);
			if (handleIndex >= 0) {
				selectedBoxFlag = true;
				selectBox(index);
				box.startResize(handleIndex, event);
				if (event.pointerType === "mouse") {
					startMouseResizeCursor(
						box.resizeHandles[handleIndex].cursor,
					);
				}
				return true;
			}
		}

		// Check if the mouse is inside a box
		for (const { box, index } of getVisibleBoxEntries()) {
			if (box.isPointInsideBox(mouseX, mouseY)) {
				selectedBoxFlag = true;
				selectBox(index);
				box.startDrag(event);
				if (event.pointerType === "mouse") {
					startMouseDragCursor();
				}
				return true;
			}
		}

		return selectedBoxFlag;
	}

	function handlePointerUp(event: PointerEvent) {
		if (!interactive) {
			return;
		}
		pointersCache.delete(event.pointerId);
		canvas.releasePointerCapture(event.pointerId);
		if (canvasWindow.isDragging) {
			canvasWindow.stopDrag();
		}
		if (pointCreationPending) {
			pointCreationPending = false;
			onPointFinishCreation();
		}
		if (event.pointerType === "mouse") {
			stopMouseResizeCursor();
			stopMouseDragCursor();
		}
		dispatch("change");
	}

	function handlePointerCancel(event: PointerEvent) {
		if (!interactive) {
			return;
		}
		pointersCache.delete(event.pointerId);
		canvas.releasePointerCapture(event.pointerId);
		if (canvasWindow.isDragging) {
			canvasWindow.stopDrag();
		}
		if (event.pointerType === "mouse") {
			stopMouseResizeCursor();
			stopMouseDragCursor();
		}
		dispatch("change");
	}

	function handlePointerMove(event: PointerEvent) {
		if (!interactive) {
			return;
		}

		event.preventDefault();
		if (event.pointerType === "mouse") {
			if (isMouseResizing) {
				canvas.style.cursor = activeResizeCursor ?? "default";
				return;
			}
			if (isMouseDragging) {
				canvas.style.cursor = "grabbing";
				return;
			}

			if (value === null) {
				return;
			}

			if (mode !== Mode.drag) {
				return;
			}

			const rect = canvas.getBoundingClientRect();
			const mouseX = event.clientX - rect.left;
			const mouseY = event.clientY - rect.top;

			// リサイズ可能箇所（ハンドル）に来たら、方向に応じた *-resize カーソルを表示
			// NOTE: handlesCursor の値に関わらず、ドラッグモードではユーザーが
			// どこでリサイズできるか分かるようにカーソルを出す
			for (const { box } of getVisibleBoxEntries()) {
				// オフセット/スケール変更直後でも hit-test がズレないように最新化
				box.updateOffset();
				const handleIndex = box.indexOfPointInsideHandle(
					mouseX,
					mouseY,
				);
				if (handleIndex >= 0) {
					canvas.style.cursor = box.resizeHandles[handleIndex].cursor;
					return;
				}
			}

			// ドラッグモード中は、ボックス上にホバーしたら手（grab）を表示
			for (const { box } of getVisibleBoxEntries()) {
				// 念のため最新化（上のループで更新済みのケースが多いが、focusSelectedOnly等で
				// ループ対象が変わる可能性があるため）
				box.updateOffset();
				if (box.isPointInsideBox(mouseX, mouseY)) {
					canvas.style.cursor = "grab";
					return;
				}
			}

			canvas.style.cursor = "default";
		} else {
			// touch
			if (!pointersCache.has(event.pointerId)) {
				return;
			}
			pointersCache.set(event.pointerId, event);

			if (pointersCache.size === 2) {
				const pointerArray = Array.from(pointersCache.values());
				const touch1 = pointerArray[0];
				const touch2 = pointerArray[1];
				const distance = getDistance(touch1, touch2);
				const rect = canvas.getBoundingClientRect();
				const centerX =
					(touch1.clientX + touch2.clientX) / 2 - rect.left;
				const centerY =
					(touch1.clientY + touch2.clientY) / 2 - rect.top;

				const newScaleTmp = parseFloat(
					(
						canvasWindow.scale *
						(distance / touchScaleValues.distance)
					).toFixed(2),
				);
				const newScale = newScaleTmp < 1 ? 1 : newScaleTmp;

				const scaleDelta = newScale / canvasWindow.scale;
				canvasWindow.offsetX =
					touchScaleValues.x -
					(touchScaleValues.x - canvasWindow.offsetX) * scaleDelta;
				canvasWindow.offsetY =
					touchScaleValues.y -
					(touchScaleValues.y - canvasWindow.offsetY) * scaleDelta;

				const dx = centerX - touchScaleValues.x;
				const dy = centerY - touchScaleValues.y;
				canvasWindow.offsetX += dx;
				canvasWindow.offsetY += dy;
				canvasWindow.scale = newScale;

				touchScaleValues.x = centerX;
				touchScaleValues.y = centerY;
				touchScaleValues.distance = distance;

				draw();
			}
		}
	}

	function resetView() {
		// Calculate minimum scale to fit image
		const scaleX = canvas.width / imageWidth;
		const scaleY = canvas.height / imageHeight;
		const minScale = Math.min(scaleX, scaleY);

		// Set scale and center
		canvasWindow.scale = minScale;
		canvasWindow.offsetX = (canvas.width - imageWidth * minScale) / 2;
		canvasWindow.offsetY = (canvas.height - imageHeight * minScale) / 2;

		draw();
	}

	function handleKeyPress(event: KeyboardEvent) {
		if (
			!enableKeyboardShortcuts ||
			event.target !== annotatorContainerDiv ||
			!interactive
		) {
			return;
		}

		const key = event.key.toLowerCase();
		const blockedKeys = new Set(["delete", "b", "c", "d", "e", "p", " "]);

		if (blockedKeys.has(key)) {
			event.preventDefault();
			event.stopPropagation();
		}

		switch (key) {
			case "delete":
				onDeleteBox();
				break;
			case "b":
				setCreateMode();
				break;
			case "c":
				handleClearSelection();
				break;
			case "p":
				setPointMode();
				break;
			case "d":
				setDragMode();
				break;
			case "e":
				onEditBox();
				break;
			case " ":
				resetView();
				break;
		}
	}

	function focusAnnotator() {
		setTimeout(() => {
			annotatorContainerDiv?.focus();
		}, 0);
	}

	function handleMouseWheel(event: WheelEvent) {
		if (!interactive) {
			return;
		}

		const isResizing =
			value?.boxes?.some((box) => box.isResizing || box.isCreating) ??
			false;
		if (isResizing) {
			event.preventDefault();
			return;
		}

		event.preventDefault();
		const delta = 1 / (1 + (event.deltaY / 1000) * 0.5);

		const newScaleTmp = parseFloat((canvasWindow.scale * delta).toFixed(2));
		const newScale = newScaleTmp < 1 ? 1 : newScaleTmp;
		const rect = canvas.getBoundingClientRect();
		const mouseX = event.clientX - rect.left;
		const mouseY = event.clientY - rect.top;

		const worldX = (mouseX - canvasWindow.offsetX) / canvasWindow.scale;
		const worldY = (mouseY - canvasWindow.offsetY) / canvasWindow.scale;

		canvasWindow.offsetX = mouseX - worldX * newScale;
		canvasWindow.offsetY = mouseY - worldY * newScale;

		if (value !== null) {
			for (const box of value.boxes) {
				if (box.isDragging) {
					box.offsetMouseX = event.clientX - box._xmin * newScale;
					box.offsetMouseY = event.clientY - box._ymin * newScale;
				}
			}
			for (const point of value.points) {
				if (point.isDragging) {
					point.offsetMouseX = event.clientX - point._x * newScale;
					point.offsetMouseY = event.clientY - point._y * newScale;
				}
			}
		}

		canvasWindow.scale = newScale;
		draw();
	}

	function createBox(event: PointerEvent) {
		const rect = canvas.getBoundingClientRect();
		const x =
			(event.clientX - rect.left - canvasWindow.offsetX) /
			scaleFactor /
			canvasWindow.scale;
		const y =
			(event.clientY - rect.top - canvasWindow.offsetY) /
			scaleFactor /
			canvasWindow.scale;
		let color;
		if (choicesColors.length > 0) {
			color = colorHexToRGB(choicesColors[0]);
		} else if (singleBox) {
			if (value.boxes.length > 0) {
				color = value.boxes[0].color;
			} else {
				color = Colors[0];
			}
		} else {
			color = Colors[value.boxes.length % Colors.length];
		}

		let box = new Box(
			drawAndNotify,
			onBoxFinishCreation,
			canvasWindow,
			pointersCache,
			canvasXmin,
			canvasYmin,
			canvasXmax,
			canvasYmax,
			"",
			x,
			y,
			x,
			y,
			color,
			boxAlpha,
			handleSize,
			boxThickness,
			boxSelectedThickness,
		);
		box.startCreating(event, rect.left, rect.top);
		if (singleBox) {
			value.boxes = [box];
		} else {
			value.boxes = [box, ...value.boxes];
		}
		selectBox(0);
		draw();
		dispatch("change");
	}

	function createPoint(event: PointerEvent) {
		const rect = canvas.getBoundingClientRect();
		const x =
			(event.clientX - rect.left - canvasWindow.offsetX) /
			canvasWindow.scale;
		const y =
			(event.clientY - rect.top - canvasWindow.offsetY) /
			canvasWindow.scale;
		let color;
		if (choicesColors.length > 0) {
			color = colorHexToRGB(choicesColors[0]);
		} else if (singleBox) {
			if (value.points.length > 0) {
				color = value.points[0].color;
			} else {
				color = Colors[0];
			}
		} else {
			color = Colors[value.points.length % Colors.length];
		}

		const point = new PointShape(
			drawAndNotify,
			canvasWindow,
			pointersCache,
			canvasXmin,
			canvasYmin,
			canvasXmax,
			canvasYmax,
			"",
			x,
			y,
			color,
			0.7,
			Math.max(4, handleSize / 2),
			scaleFactor,
		);
		if (singleBox) {
			value.points = [point];
		} else {
			value.points = [point, ...value.points];
		}
		selectPoint(0);
		point.startDrag(event);
		pointCreationPending = true;
		draw();
		dispatch("change");
	}

	function clickSelection(event: PointerEvent) {
		const hitBox = clickBox(event);
		if (hitBox) {
			return;
		}

		const rect = canvas.getBoundingClientRect();
		const mouseX = event.clientX - rect.left;
		const mouseY = event.clientY - rect.top;
		for (const { point, index } of getVisiblePointEntries()) {
			if (point.isPointInsidePoint(mouseX, mouseY)) {
				selectPoint(index);
				point.startDrag(event);
				if (event.pointerType === "mouse") {
					startMouseDragCursor();
				}
				return;
			}
		}

		const preserveSelection = focusSelectedOnly || selectedAnnotationId;
		if (!singleBox && !preserveSelection) {
			handleClearSelection();
		}

		canvasWindow.startDrag(event);
		if (event.pointerType === "mouse") {
			startMouseDragCursor();
		}
	}

	function clearFocusSelection() {
		if (focusSelectedOnly || selectedAnnotationId) {
			onClearSelection?.();
		}
		selectedAnnotationId = null;
		focusSelectedOnly = false;
		selectedInfo = null;
		lastSelectedAnnotationId = null;
		selectedTarget = null;
		selectedBox = -1;
		selectedPoint = -1;
		value?.boxes.forEach((box) => box.setSelected(false));
		value?.points.forEach((point) => point.setSelected(false));
	}

	function setCreateMode() {
		clearFocusSelection();
		mode = Mode.creation;
		stopMouseDragCursor();
		draw();
	}

	function setPointMode() {
		clearFocusSelection();
		mode = Mode.point;
		stopMouseDragCursor();
		draw();
	}

	function setDragMode() {
		mode = Mode.drag;
		stopMouseDragCursor();
		draw();
	}

	function handleClearSelection() {
		onClearSelection?.();
		selectedAnnotationId = null;
		focusSelectedOnly = false;
		selectedInfo = null;
		lastSelectedAnnotationId = null;
		selectedTarget = null;
		selectedBox = -1;
		selectedPoint = -1;
		value?.boxes.forEach((box) => box.setSelected(false));
		value?.points.forEach((point) => point.setSelected(false));
		draw();
	}

	function onBoxFinishCreation() {
		if (selectedBox >= 0 && selectedBox < value.boxes.length) {
			if (value.boxes[selectedBox].getArea() < 1) {
				onDeleteBox();
			} else {
				if (!disableEditBoxes) {
					if (labelDetailLock) {
						onUseDefaultLabelModalNew();
					} else {
						newModalVisible = true;
					}
				}
				if (singleBox) {
					setDragMode();
				}
			}
		}
	}

	function onPointFinishCreation() {
		if (selectedPoint >= 0 && selectedPoint < value.points.length) {
			if (!disableEditBoxes) {
				if (labelDetailLock) {
					onUseDefaultLabelModalNew();
				} else {
					newModalVisible = true;
				}
			}
			if (singleBox) {
				setDragMode();
			}
		}
	}

	function onEditBox() {
		if (!disableEditBoxes) {
			if (selectedTarget === "box") {
				if (selectedBox >= 0 && selectedBox < value.boxes.length) {
					editModalVisible = true;
				}
			} else if (selectedTarget === "point") {
				if (selectedPoint >= 0 && selectedPoint < value.points.length) {
					editModalVisible = true;
				}
			}
		}
	}

	function handleDoubleClick(event: MouseEvent) {
		if (!interactive) {
			return;
		}

		onEditBox();
	}

	function onModalEditChange(event) {
		editModalVisible = false;
		focusAnnotator();
		const { detail } = event;
		const label = detail.label;
		const color = detail.color;
		const ret = detail.ret;
		if (selectedTarget === "box") {
			if (selectedBox >= 0 && selectedBox < value.boxes.length) {
				const box = value.boxes[selectedBox];
				if (ret == 1) {
					box.label = label;
					box.color = colorHexToRGB(color);
					draw();
					dispatch("change");
				} else if (ret == -1) {
					onDeleteBox();
				}
			}
		} else if (selectedTarget === "point") {
			if (selectedPoint >= 0 && selectedPoint < value.points.length) {
				const point = value.points[selectedPoint];
				if (ret == 1) {
					point.label = label;
					point.color = colorHexToRGB(color);
					draw();
					dispatch("change");
				} else if (ret == -1) {
					onDeleteBox();
				}
			}
		}
	}

	function onModalNewChange(event) {
		newModalVisible = false;
		focusAnnotator();
		const { detail } = event;
		const label = detail.label;
		const color = detail.color;
		const ret = detail.ret;
		const lock = detail.lock;
		if (selectedTarget === "box") {
			if (selectedBox >= 0 && selectedBox < value.boxes.length) {
				const box = value.boxes[selectedBox];
				if (ret == 1) {
					labelDetailLock = lock;
					defaultLabelCache.label = label;
					defaultLabelCache.color = color;
					box.label = label;
					box.color = colorHexToRGB(color);
					draw();
					dispatch("change");
				} else {
					onDeleteBox();
				}
			}
		} else if (selectedTarget === "point") {
			if (selectedPoint >= 0 && selectedPoint < value.points.length) {
				const point = value.points[selectedPoint];
				if (ret == 1) {
					labelDetailLock = lock;
					defaultLabelCache.label = label;
					defaultLabelCache.color = color;
					point.label = label;
					point.color = colorHexToRGB(color);
					draw();
					dispatch("change");
				} else {
					onDeleteBox();
				}
			}
		}
	}

	function onDefaultLabelEditChange(event) {
		editDefaultLabelVisible = false;
		focusAnnotator();
		const { detail } = event;
		let label = detail.label;
		let color = detail.color;
		let ret = detail.ret;
		let lock = detail.lock;
		if (ret == 1) {
			labelDetailLock = lock;
			defaultLabelCache.label = label;
			defaultLabelCache.color = color;
		}
	}

	function onUseDefaultLabelModalNew() {
		if (selectedTarget === "box") {
			if (selectedBox >= 0 && selectedBox < value.boxes.length) {
				const box = value.boxes[selectedBox];
				box.label = defaultLabelCache.label;
				if (defaultLabelCache.color !== "") {
					box.color = colorHexToRGB(defaultLabelCache.color);
				}
				draw();
				dispatch("change");
			}
		} else if (selectedTarget === "point") {
			if (selectedPoint >= 0 && selectedPoint < value.points.length) {
				const point = value.points[selectedPoint];
				point.label = defaultLabelCache.label;
				if (defaultLabelCache.color !== "") {
					point.color = colorHexToRGB(defaultLabelCache.color);
				}
				draw();
				dispatch("change");
			}
		}
	}

	function onDeleteBox() {
		if (selectedTarget === "box") {
			if (selectedBox >= 0 && selectedBox < value.boxes.length) {
				value.boxes.splice(selectedBox, 1);
				selectBox(-1);
				if (singleBox) {
					setCreateMode();
				}
				dispatch("change");
			}
		} else if (selectedTarget === "point") {
			if (selectedPoint >= 0 && selectedPoint < value.points.length) {
				value.points.splice(selectedPoint, 1);
				selectPoint(-1);
				if (singleBox) {
					setCreateMode();
				}
				dispatch("change");
			}
		}
	}

	/**
	 * Rotate the image and all the boxes
	 * @param op 1: rotate clockwise, -1: rotate counterclockwise
	 */
	function onRotateImage(op: number) {
		value.orientation = (((value.orientation + op) % 4) + 4) % 4;
		canvasWindow.orientation = value.orientation;

		resize();
		for (const box of value.boxes) {
			box.onRotate(op);
		}
		for (const point of value.points) {
			point.onRotate(op);
		}
		draw();
		dispatch("change");
	}

	function resize() {
		if (canvas) {
			scaleFactor = 1;
			canvas.width = canvas.clientWidth;

			canvasWindow.setRotatedImage(image);

			if (image !== null) {
				if (canvasWindow.imageRotatedWidth > canvas.width) {
					scaleFactor = canvas.width / canvasWindow.imageRotatedWidth;
					imageWidth = Math.round(
						canvasWindow.imageRotatedWidth * scaleFactor,
					);
					imageHeight = Math.round(
						canvasWindow.imageRotatedHeight * scaleFactor,
					);
					canvasXmin = 0;
					canvasYmin = 0;
					canvasXmax = imageWidth;
					canvasYmax = imageHeight;
					canvas.height = imageHeight;
				} else {
					imageWidth = canvasWindow.imageRotatedWidth;
					imageHeight = canvasWindow.imageRotatedHeight;
					var x = (canvas.width - imageWidth) / 2;
					canvasXmin = x;
					canvasYmin = 0;
					canvasXmax = x + imageWidth;
					canvasYmax = imageHeight;
					canvas.height = imageHeight;
				}

				canvasWindow.imageWidth = imageWidth;
				canvasWindow.imageHeight = imageHeight;
			} else {
				canvasXmin = 0;
				canvasYmin = 0;
				canvasXmax = canvas.width;
				canvasYmax = canvas.height;
				canvas.height = canvas.clientHeight;
			}

			canvasWindow.resize(
				canvas.width,
				canvas.height,
				canvasXmin,
				canvasYmin,
			);

			if (canvasXmax > 0 && canvasYmax > 0) {
				for (const box of value.boxes) {
					box.canvasXmin = canvasXmin;
					box.canvasYmin = canvasYmin;
					box.canvasXmax = canvasXmax;
					box.canvasYmax = canvasYmax;
					box.setScaleFactor(scaleFactor);
				}
				for (const point of value.points) {
					point.canvasXmin = canvasXmin;
					point.canvasYmin = canvasYmin;
					point.canvasXmax = canvasXmax;
					point.canvasYmax = canvasYmax;
					point.setScaleFactor(scaleFactor);
				}
			}
			draw();
			dispatch("change");
		}
	}
	const observer = new ResizeObserver(resize);

	function parseInputBoxes() {
		for (let i = 0; i < value.boxes.length; i++) {
			let box = value.boxes[i];
			if (!(box instanceof Box)) {
				const rawBox = box as Record<string, unknown>;
				let color = "";
				let label = "";
				if (Object.prototype.hasOwnProperty.call(rawBox, "color")) {
					color = rawBox["color"] as string;
					if (Array.isArray(color) && color.length === 3) {
						color = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
					}
				} else {
					color = Colors[i % Colors.length];
				}
				if (Object.prototype.hasOwnProperty.call(rawBox, "label")) {
					label = rawBox["label"] as string;
				}
				box = new Box(
					drawAndNotify,
					onBoxFinishCreation,
					canvasWindow,
					pointersCache,
					canvasXmin,
					canvasYmin,
					canvasXmax,
					canvasYmax,
					label,
					rawBox["xmin"] as number,
					rawBox["ymin"] as number,
					rawBox["xmax"] as number,
					rawBox["ymax"] as number,
					color,
					boxAlpha,
					handleSize,
					boxThickness,
					boxSelectedThickness,
				);
				value.boxes[i] = box;
			}
		}
	}

	function parseInputPoints() {
		for (let i = 0; i < value.points.length; i++) {
			let point = value.points[i];
			if (!(point instanceof PointShape)) {
				const rawPoint = point as Record<string, unknown>;
				let color = "";
				let label = "";
				if (Object.prototype.hasOwnProperty.call(rawPoint, "color")) {
					color = rawPoint["color"] as string;
					if (Array.isArray(color) && color.length === 3) {
						color = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
					}
				} else {
					color = Colors[i % Colors.length];
				}
				if (Object.prototype.hasOwnProperty.call(rawPoint, "label")) {
					label = rawPoint["label"] as string;
				}
				point = new PointShape(
					drawAndNotify,
					canvasWindow,
					pointersCache,
					canvasXmin,
					canvasYmin,
					canvasXmax,
					canvasYmax,
					label,
					rawPoint["x"] as number,
					rawPoint["y"] as number,
					color,
					0.7,
					Math.max(4, handleSize / 2),
					scaleFactor,
				);
				value.points[i] = point;
			}
		}
	}

	$: {
		value;
		canvasWindow.orientation = value.orientation;
		setImage();
		parseInputBoxes();
		parseInputPoints();
		resize();
		draw();
	}

	function setImage() {
		if (imageUrl !== null) {
			if (image === null || image.src != imageUrl) {
				image = new Image();
				image.src = imageUrl;
				image.onload = function () {
					resize();
					draw();
				};
			}
		}
	}

	onMount(() => {
		if (Array.isArray(choices) && choices.length > 0) {
			if (!Array.isArray(choicesColors) || choicesColors.length == 0) {
				for (let i = 0; i < choices.length; i++) {
					let color = Colors[i % Colors.length];
					choicesColors.push(colorRGBAToHex(color));
				}
			}
			defaultLabelCache.label = choices[0][0];
			defaultLabelCache.color = choicesColors[0];
		}

		ctx = canvas.getContext("2d");
		observer.observe(canvas);

		if (selectedBox < 0 && value !== null && value.boxes.length > 0) {
			selectBox(0);
		}
		if (selectedPoint < 0 && value !== null && value.points.length > 0) {
			selectPoint(0);
		}

		setImage();
		resize();
		draw();
	});
</script>

<!-- svelte-ignore a11y-no-noninteractive-tabindex -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<div
	class="annotator-container"
	tabindex="0"
	bind:this={annotatorContainerDiv}
	on:keydown={handleKeyPress}
	on:click={() => annotatorContainerDiv.focus()}
>
	<div class="canvas-container">
		<canvas
			bind:this={canvas}
			on:pointerdown={handlePointerDown}
			on:pointerup={handlePointerUp}
			on:pointermove={handlePointerMove}
			on:pointercancel={handlePointerCancel}
			on:dblclick={handleDoubleClick}
			on:wheel={handleMouseWheel}
			style="height: {height}; width: {width};"
			class="canvas-annotator"
		></canvas>
	</div>

	{#if interactive}
		<span class="canvas-control">
			<button
				class="icon"
				class:selected={mode === Mode.creation}
				aria-label="Create box"
				title="Create box (C)"
				on:click={() => setCreateMode()}><BoundingBox /></button
			>
			<button
				class="icon"
				class:selected={mode === Mode.point}
				aria-label="Create point"
				title="Create point (C)"
				on:click={() => setPointMode()}><Point /></button
			>
			<button
				class="icon"
				class:selected={mode === Mode.drag}
				aria-label="Drag boxes"
				title="Drag boxes (D)"
				on:click={() => setDragMode()}><Hand /></button
			>
			<button
				class="icon"
				aria-label="Clear selection"
				title="Clear selection"
				on:click={handleClearSelection}
				disabled={!selectedAnnotationId}
			>
				<Clear />
			</button>
			{#if showRemoveButton}
				<button
					class="icon"
					aria-label="Remove box"
					title="Remove box (Del)"
					on:click={() => onDeleteBox()}><Trash /></button
				>
			{/if}
			{#if !disableEditBoxes && labelDetailLock}
				<button
					class="icon"
					aria-label="Edit label"
					title="Edit label"
					on:click={() => (editDefaultLabelVisible = true)}
					><Label /></button
				>
			{/if}
			<button
				class="icon"
				aria-label="Rotate counterclockwise"
				title="Rotate counterclockwise"
				on:click={() => onRotateImage(-1)}><Undo /></button
			>
			<button
				class="icon"
				aria-label="Rotate clockwise"
				title="Rotate clockwise"
				on:click={() => onRotateImage(1)}><Redo /></button
			>
		</span>
	{/if}
</div>

{#if editModalVisible}
	<ModalBox
		on:change={onModalEditChange}
		on:enter{onModalEditChange}
		{choices}
		{choicesColors}
		label={selectedLabel}
		color={selectedColor}
	/>
{/if}

{#if newModalVisible}
	<ModalBox
		on:change={onModalNewChange}
		on:enter{onModalNewChange}
		{choices}
		showRemove={false}
		{choicesColors}
		label={selectedLabel}
		color={selectedColor}
		{labelDetailLock}
	/>
{/if}

{#if editDefaultLabelVisible}
	<ModalBox
		on:change={onDefaultLabelEditChange}
		on:enter{onDefaultLabelEditChange}
		{choices}
		showRemove={false}
		{choicesColors}
		label={defaultLabelCache.label}
		color={defaultLabelCache.color}
		{labelDetailLock}
	/>
{/if}

<style>
	.canvas-annotator {
		border-color: var(--block-border-color);
		width: 100%;
		height: 100%;
		display: block;
		touch-action: none;
	}

	.canvas-control {
		display: flex;
		align-items: center;
		justify-content: center;
		border-top: 1px solid var(--border-color-primary);
		width: 95%;
		bottom: 0;
		left: 0;
		right: 0;
		margin-left: auto;
		margin-right: auto;
		margin-top: var(--size-2);
	}

	.icon {
		width: 22px;
		height: 22px;
		margin: var(--spacing-lg) var(--spacing-xs);
		padding: var(--spacing-xs);
		color: var(--neutral-400);
		border-radius: var(--radius-md);
		border: none;
		background: transparent;
		cursor: pointer;
	}

	.icon:disabled {
		opacity: 0.45;
		cursor: default;
	}

	.icon:disabled:hover,
	.icon:disabled:focus {
		color: var(--neutral-400);
	}

	.icon:hover,
	.icon:focus {
		color: var(--color-accent);
	}

	.selected {
		color: var(--color-accent);
	}

	.canvas-container {
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.canvas-container:focus {
		outline: none;
	}
</style>
