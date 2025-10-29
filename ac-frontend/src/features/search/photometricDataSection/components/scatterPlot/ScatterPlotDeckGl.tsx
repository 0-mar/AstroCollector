import React, {useEffect, useMemo, useRef, useState} from "react";
import DeckGL from "@deck.gl/react";
import { ScatterplotLayer } from "@deck.gl/layers";
import {
    OrthographicView,
    COORDINATE_SYSTEM,
    type OrthographicViewState,
    OrthographicViewport,
    LinearInterpolator
} from "@deck.gl/core";
import {DataFilterExtension} from '@deck.gl/extensions';
import type { PhotometricDataDto } from "../../types";
import {Button} from "@/../components/ui/button.tsx";
import AxesGridLayer from "@/features/search/photometricDataSection/components/scatterPlot/AxesGridLayer.ts";
import type {ZoomCords} from "@/features/search/photometricDataSection/components/plotOptions/OptionsContext.tsx";


const PADDING = { left: 80, bottom: 44, right: 12, top: 8 };

function fitViewXY(innerW: number, innerH: number,
                   xMin: number, xMax: number, yMin: number, yMax: number
): OrthographicViewState {
    const xRange = Math.max(1e-9, xMax - xMin);
    const yRange = Math.max(1e-9, yMax - yMin);

    const scaleX = innerW / xRange;
    const scaleY = innerH / yRange;

    const zoomX = Math.log2(0.95 * scaleX);
    const zoomY = Math.log2(0.95 * scaleY);

    return {
        target: [(xMin + xMax) / 2, (yMin + yMax) / 2, 0],
        zoom: [zoomX, zoomY],
        //minZoom: -20,
        //maxZoom: 12
    };
}

type ScatterPlotDeckGLProps = {
    data: PhotometricDataDto[],
    colorFn: (dto: PhotometricDataDto) => [number, number, number],
    xDataFn: (dto: PhotometricDataDto) => number,
    tooltipFn: (dto: PhotometricDataDto | null) => {text: string} | null,
    xTitle: string,
    yTitle: string,
    filterCategories: any[],
    filterCategoryFn: (dto: PhotometricDataDto) => any,
    zoomToCoords: ZoomCords | null,
}

type Domain = { xMin:number; xMax:number; yMin:number; yMax:number; errMin:number; errMax:number };

import {OrthographicController} from '@deck.gl/core';

class QZoomWheelController extends OrthographicController {
    constructor(props) {
        super(props);
    }

    handleEvent(event) {
        if (event.type === 'wheel') {
            if (!this.props?.allowWheelZoom) return;
        }
        super.handleEvent(event);
    }

}

const ScatterPlotDeckGl = ({data, xTitle, yTitle, colorFn, tooltipFn, xDataFn, filterCategories, filterCategoryFn, zoomToCoords}: ScatterPlotDeckGLProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const [size, setSize] = useState({w: 800, h: 480});
    const [viewState, setViewState] = useState<OrthographicViewState>({target: [0,0,0], zoom: [0, 0]});

    const [qDown, setQDown] = useState(false);

    useEffect(() => {
        const onDown = (e: KeyboardEvent) => {
            if (e.key.toLowerCase() === 'q') setQDown(true);
        };
        const onUp = (e: KeyboardEvent) => {
            if (e.key.toLowerCase() === 'q') setQDown(false);
        };
        window.addEventListener('keydown', onDown);
        window.addEventListener('keyup', onUp);
        return () => {
            window.removeEventListener('keydown', onDown);
            window.removeEventListener('keyup', onUp);
        };
    }, []);

    // get plot canvas size
    useEffect(() => {
        const el = ref.current!;
        const ro = new ResizeObserver(() => {
            const r = el.getBoundingClientRect();
            setSize({w: Math.max(1, r.width), h: Math.max(1, r.height)});
        });
        ro.observe(el);
        const r = el.getBoundingClientRect();
        setSize({w: Math.max(1, r.width), h: Math.max(1, r.height)});
        return () => ro.disconnect();
    }, []);

    // handle plot zooming
    const [zoomed, setZoomed] = useState(false);
    useEffect(() => {
        if (zoomToCoords === null) {
            return;
        }
        const innerW = size.w - PADDING.left - PADDING.right;
        const innerH = size.h - PADDING.top - PADDING.bottom;
        setViewState(v => (
            {
                ...v,
                ...fitViewXY(innerW, innerH, zoomToCoords.xMin, zoomToCoords.xMax, zoomToCoords.yMin, zoomToCoords.yMax),
                transitionDuration: 250,
                transitionInterpolator: new LinearInterpolator(['target', 'zoom'])
            }));
        setZoomed(true);
    }, [zoomToCoords]);

    // compute data domain
    const lastNonEmptyDomRef = useRef<Domain | null>(null);
    const dom = useMemo<Domain>(() => {
        // default domain when no data are present
        if (!data.length) {
            return { xMin: 0, xMax: 100, yMin: -10, yMax: 0, errMin: 0, errMax: 5 };
        }

        let xMin =  Infinity, xMax = -Infinity;
        let magMin =  Infinity, magMax = -Infinity;
        let errMin =  Infinity, errMax = -Infinity;
        let containsData = false;

        for (let i = 0; i < data.length; i++) {
            const d = data[i];
            const cat = filterCategoryFn(d);

            // filter out data
            if (!filterCategories.includes(cat)) {
                continue;
            }

            const x = xDataFn(d);
            if (x < xMin) {
                xMin = x;
            }
            if (x > xMax) {
                xMax = x;
            }

            const m = d.magnitude;
            if (m < magMin) {
                magMin = m;
            }
            if (m > magMax) {
                magMax = m;
            }

            const e = d.magnitude_error;
            if (e < errMin) {
                errMin = e;
            }
            if (e > errMax) {
                errMax = e;
            }

            containsData = true;
        }

        if (!containsData) {
            // nothing visible -> keep the last non-empty domain or a sensible fallback
            return lastNonEmptyDomRef.current ?? { xMin: 0, xMax: 100, yMin: 0, yMax: 20, errMin: 0, errMax: 5 };
        }

        const domain = { xMin, xMax, yMin: magMin, yMax: magMax, errMin, errMax };
        lastNonEmptyDomRef.current = domain;
        return domain;
    }, [data, xDataFn, filterCategoryFn, filterCategories]);

    // initial fit of all data points (to the inner plot area)
    const autoFit = () => {
        if (!dom) return;
        const innerW = size.w - PADDING.left - PADDING.right;
        const innerH = size.h - PADDING.top - PADDING.bottom;
        setViewState(v => (
            {
                ...v,
                ...fitViewXY(innerW, innerH, dom.xMin, dom.xMax, dom.yMin, dom.yMax),
                transitionDuration: 250,
                transitionInterpolator: new LinearInterpolator(['target', 'zoom'])
            }));
    }
    useEffect(() => {
        if (zoomed) {
            setZoomed(false);
            return;
        }
        autoFit();
    }, [dom, size.w, size.h]);

    // plot layers
    const layers = useMemo(() => {
        if (!dom) {
            return [];
        }

        return [
            new AxesGridLayer({
                id: 'axes',
                xFormat: (x) => x.toFixed(2),
                yFormat: (y) => (y).toFixed(2),
                xTitle: xTitle,
                yTitle: yTitle,
                paddingPx: PADDING,
                labelOffsetPx: 6
            }),
            new ScatterplotLayer<PhotometricDataDto>({
                id: 'points',
                data,
                coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
                getPosition: d => [xDataFn(d), d.magnitude, 0],
                radiusUnits: 'pixels',
                getRadius: () => 5,
                getFillColor: d => {
                    const [r,g,b] = colorFn(d)
                    return [r, g, b, 200];
                },
                pickable: true,
                autoHighlight: true,
                getFilterCategory: filterCategoryFn,
                filterCategories: filterCategories,
                extensions: [new DataFilterExtension({categorySize: 1})],
                updateTriggers: {
                    getFillColor: [colorFn],
                    filterCategories: [filterCategories],
                    getFilterCategory: [filterCategoryFn],
                    getPosition: [xDataFn],
                }
            })
        ];
    }, [data, dom, filterCategories, /*filterCategoryFn, colorFn*/]);

    // =====================================================
    // Shift + Drag box zoom
    // =====================================================
    const [shift, setShift] = useState(false);
    const [brush, setBrush] = useState<null | {x0:number; y0:number; x1:number; y1:number}>(null);

    // shift key listener
    useEffect(() => {
        const down = (e: KeyboardEvent) => { if (e.key === 'Shift') setShift(true); };
        const up   = (e: KeyboardEvent) => { if (e.key === 'Shift') setShift(false); };
        window.addEventListener('keydown', down);
        window.addEventListener('keyup', up);
        return () => { window.removeEventListener('keydown', down); window.removeEventListener('keyup', up); };
    }, []);

    // clamp a pixel point to the inner plot rectangle
    const clampToInner = (px:number, py:number) => {
        const left = PADDING.left, right = size.w - PADDING.right;
        const top = PADDING.top, bottom = size.h - PADDING.bottom;
        const x = Math.max(left, Math.min(right, px));
        const y = Math.max(top, Math.min(bottom, py));
        return [x, y] as const;
    };

    const onMouseDown = (e: React.MouseEvent) => {
        if (!shift) {
            return; // normal pan without shift
        }
        e.preventDefault();
        const rect = ref.current!.getBoundingClientRect();
        const px = e.clientX - rect.left;
        const py = e.clientY - rect.top;
        const [x0, y0] = clampToInner(px, py);
        setBrush({x0, y0, x1: x0, y1: y0});
    };

    const onMouseMove = (e: React.MouseEvent) => {
        if (!brush) return;
        const rect = ref.current!.getBoundingClientRect();
        const px = e.clientX - rect.left;
        const py = e.clientY - rect.top;
        const [x1, y1] = clampToInner(px, py);
        setBrush(b => b ? {...b, x1, y1} : b);
    };

    const finishZoom = (b: {x0:number;y0:number;x1:number;y1:number}) => {
        const xMinPx = Math.min(b.x0, b.x1);
        const xMaxPx = Math.max(b.x0, b.x1);
        const yMinPx = Math.min(b.y0, b.y1);
        const yMaxPx = Math.max(b.y0, b.y1);
        if (xMaxPx - xMinPx < 4 || yMaxPx - yMinPx < 4) {
            return; // too small
        }

        const vp = new OrthographicViewport({...viewState, width: size.w, height: size.h});

        // unproject both corners, then sort to zoom
        const [xa, ya] = vp.unproject([xMinPx, yMinPx]);
        const [xb, yb] = vp.unproject([xMaxPx, yMaxPx]);

        const xMin = Math.min(xa, xb);
        const xMax = Math.max(xa, xb);
        const yMin = Math.min(ya, yb);
        const yMax = Math.max(ya, yb);

        const innerW = size.w - PADDING.left - PADDING.right;
        const innerH = size.h - PADDING.top - PADDING.bottom;

        const next = fitViewXY(innerW, innerH, xMin, xMax, yMin, yMax);

        setViewState(v => ({
            ...v,
            ...next,
            transitionDuration: 250,
            transitionInterpolator: new LinearInterpolator(['target', 'zoom'])
        }));
    };

    const onMouseUp = () => {
        if (brush) {
            finishZoom(brush);
        }
        setBrush(null);
    };

    const onKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Escape') {
            setBrush(null);
        }
    };

    const brushRect = brush && {
        left: Math.min(brush.x0, brush.x1),
        top: Math.min(brush.y0, brush.y1),
        width: Math.abs(brush.x1 - brush.x0),
        height: Math.abs(brush.y1 - brush.y0)
    };

    return (
        <div className={"flex flex-col gap-y-2 min-h-[520px"}>

            <div
                ref={ref}
                // height must be set, otherwise graph layer throws errors
                style={{ width: '100%', height: 500, position: 'relative' }}
                onMouseDown={onMouseDown}
                onMouseMove={onMouseMove}
                onMouseUp={onMouseUp}
                onKeyDown={onKeyDown}
                tabIndex={0} // to receive Esc
            >
                <DeckGL
                    views={new OrthographicView({id: 'ortho'})}
                    // disable pan/scroll while holding shift so brush isnt fighting the controller
                    controller={{type: QZoomWheelController, allowWheelZoom: qDown, dragPan: !shift, scrollZoom: !shift}}
                    layers={layers}
                    viewState={viewState}
                    onViewStateChange={({viewState}) => setViewState(viewState as OrthographicViewState)}
                    width={size.w}
                    height={size.h}
                    getCursor={() => (shift ? 'crosshair' : 'grab')}
                    getTooltip={({object}) => tooltipFn(object)}
                />

                {/* brush rectangle overlay (only while dragging) */}
                {brushRect && (
                    <div
                        style={{
                            position: 'absolute',
                            left: brushRect.left,
                            top: brushRect.top,
                            width: brushRect.width,
                            height: brushRect.height,
                            border: '1px solid #60a5fa',
                            background: 'rgba(96,165,250,0.15)',
                            pointerEvents: 'none'
                        }}
                    />
                )}
            </div>
            {/* control panel */}
            <div className={"flex flex-row justify-center gap-x-2 py-2"}>
                <Button onClick={() => autoFit()}>Reset</Button>
                <div
                    className="inline-flex items-center rounded-md bg-black/50 text-white text-base px-3 py-1 pointer-events-none"
                >
                    {data.length.toLocaleString()} pts · pan (drag) · zoom (Q+wheel) · box-zoom (Shift+drag)
                </div>
            </div>
        </div>
    );
}

export default ScatterPlotDeckGl;
