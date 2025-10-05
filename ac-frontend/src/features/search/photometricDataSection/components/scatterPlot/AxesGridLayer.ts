// AxesGridLayer.ts
import {CompositeLayer, type LayerContext, type DefaultProps, COORDINATE_SYSTEM} from '@deck.gl/core';
import {PathLayer, TextLayer} from '@deck.gl/layers';
import {scaleLinear} from 'd3-scale';

type AxesGridLayerProps = {
    xFormat?: (x: number) => string;
    yFormat?: (y: number) => string;
    tickCount?: number;
    axisColor?: [number, number, number, number];
    gridColor?: [number, number, number, number];
    labelColor?: [number, number, number, number];
    xTitle?: string;
    yTitle?: string;
    /** Extra space inside the plot, in pixels */
    paddingPx?: { left?: number; right?: number; top?: number; bottom?: number };
    /** How far to nudge tick labels inward, in pixels */
    labelOffsetPx?: number;
};

const defaultProps: DefaultProps<AxesGridLayerProps> = {
    xFormat: {type: 'function', value: (x: number) => x.toString()},
    yFormat: {type: 'function', value: (y: number) => y.toString()},
    tickCount: {type: 'number', value: 8},
    axisColor: {type: 'array', value: [156, 163, 175, 255]}, // gray-400
    gridColor: {type: 'array', value: [229, 231, 235, 255]}, // gray-200
    labelColor: {type: 'array', value: [55, 65, 81, 255]},   // gray-700
    xTitle: {type: 'string', value: ''},
    yTitle: {type: 'string', value: ''},
    paddingPx: {
        type: 'object',
        value: { left: 40, right: 12, top: 8, bottom: 24 }      // <- sensible defaults
    },
    labelOffsetPx: { type: 'number', value: 6 },
};

export default class AxesGridLayer extends CompositeLayer<AxesGridLayerProps> {
    static layerName = 'AxesGridLayer';
    static defaultProps = defaultProps;

    // recompute on pan/zoom or prop changes
    shouldUpdateState({changeFlags}: any) {
        return changeFlags.propsOrDataChanged || changeFlags.viewportChanged;
    }

    private getVisibleDomain(context: LayerContext) {
        const vp: any = context.viewport;
        const [xMin, yMax] = vp.unproject([0, 0]);                    // top-left
        const [xMax, yMin] = vp.unproject([vp.width, vp.height]);     // bottom-right
        return {xMin, xMax, yMin, yMax, width: vp.width, height: vp.height};
    }

    renderLayers() {
        const {
            xFormat, yFormat, tickCount,
            axisColor, gridColor, labelColor,
            xTitle, yTitle, paddingPx = {}, labelOffsetPx = 6
        } = this.props;

        const pad = {
            left:  paddingPx.left  ?? 40,
            right: paddingPx.right ?? 12,
            top:   paddingPx.top   ?? 8,
            bottom:paddingPx.bottom?? 24,
        };

        const {xMin, xMax, yMin, yMax, width, height} = this.getVisibleDomain(this.context);

        // data -> pixel scales over the full visible domain
        const xScalePx = scaleLinear().domain([xMin, xMax]).range([0, width]);
        const yScalePx = scaleLinear().domain([yMin, yMax]).range([height, 0]);

        // convert pixel padding to data coordinates
        const xInnerMin = xScalePx.invert(pad.left);
        const xInnerMax = xScalePx.invert(width - pad.right);
        const yInnerMin = yScalePx.invert(height - pad.bottom);
        const yInnerMax = yScalePx.invert(pad.top);

        // Tick generators on the inner domain (so grid/labels stay inside)
        const xInnerScalePx = scaleLinear().domain([xInnerMin, xInnerMax]).range([pad.left, width - pad.right]);
        const yInnerScalePx = scaleLinear().domain([yInnerMin, yInnerMax]).range([height - pad.bottom, pad.top]);

        const xTicks = xInnerScalePx.ticks(tickCount!);
        const yTicks = yInnerScalePx.ticks(tickCount!);

        // grid lines across the inner rect
        const gridData = [
            ...xTicks.map(t => ({path: [[t, yInnerMin, 0], [t, yInnerMax, 0]]})),
            ...yTicks.map(t => ({path: [[xInnerMin, t, 0], [xInnerMax, t, 0]]}))
        ];

        // axes at inner edges
        const axesData = [
            {path: [[xInnerMin, yInnerMin, 0], [xInnerMax, yInnerMin, 0]]}, // bottom x-axis
            {path: [[xInnerMin, yInnerMin, 0], [xInnerMin, yInnerMax, 0]]}, // left y-axis
        ];

        const xLabelData = xTicks.map(t => ({
            position: [t, yInnerMin, 0],
            text: xFormat!(t),
            // push labels outside the plot
            pixelOffset: [0, labelOffsetPx + 10],
            textAnchor: 'middle' as const,
            alignmentBaseline: 'top' as const
        }));

        const yLabelData = yTicks.map(t => ({
            position: [xInnerMin, t, 0],
            text: yFormat!(t),
            // push labels outside the plot)
            pixelOffset: [-(labelOffsetPx + 25), 0],
            textAnchor: 'end' as const,
            alignmentBaseline: 'center' as const
        }));

        // --- titles (each in its own TextLayer so we can rotate Y) ---
        type AxisTitleData = { position: [number, number, number]; text: string; pixelOffset: [number, number] };

        // X axis title - centered, below the axis
        const xTitleData: AxisTitleData[] = xTitle
            ? [{
                position: [(xInnerMin + xInnerMax) / 2, yInnerMin, 0],
                text: xTitle,
                pixelOffset: [0, pad.bottom - 7]
            }]
            : [];

        // Y axis title - centered, left of the axis
        const yTitleData: AxisTitleData[] = yTitle
            ? [{
                position: [xInnerMin, (yInnerMin + yInnerMax) / 2, 0],
                text: yTitle,
                pixelOffset: [-(pad.left - 12), 0]
            }]
            : [];

        return [
            new PathLayer({
                id: `${this.props.id || 'axes'}-grid`,
                data: gridData,
                coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
                getPath: d => d.path,
                getColor: gridColor!,
                getWidth: 1,
                widthUnits: 'pixels',
                pickable: false,
                parameters: {depthTest: false}
            }),
            new PathLayer({
                id: `${this.props.id || 'axes'}-axes`,
                data: axesData,
                coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
                getPath: d => d.path,
                getColor: axisColor!,
                getWidth: 1.25,
                widthUnits: 'pixels',
                pickable: false,
                parameters: {depthTest: false}
            }),
            new TextLayer({
                id: `${this.props.id || 'axes'}-xlabels`,
                data: xLabelData,
                coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
                getPosition: d => d.position,
                getText: d => d.text,
                getSize: 12,
                getColor: labelColor!,
                sizeUnits: 'pixels',
                getPixelOffset: d => d.pixelOffset,
                textAnchor: d => d.textAnchor,
                alignmentBaseline: d => d.alignmentBaseline,
                pickable: false,
                parameters: {depthTest: false}
            }),
            new TextLayer({
                id: `${this.props.id || 'axes'}-ylabels`,
                data: yLabelData,
                coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
                getPosition: d => d.position,
                getText: d => d.text,
                getSize: 12,
                getColor: labelColor!,
                sizeUnits: 'pixels',
                getPixelOffset: d => d.pixelOffset,
                textAnchor: d => d.textAnchor,
                alignmentBaseline: d => d.alignmentBaseline,
                pickable: false,
                parameters: {depthTest: false}
            }),
            xTitleData.length > 0 && new TextLayer({
                id: `${this.props.id || 'axes'}-xtitle`,
                data: xTitleData,
                coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
                getPosition: d => d.position,
                getText: d => d.text,
                getSize: 12,
                getColor: labelColor!,
                sizeUnits: 'pixels',
                getPixelOffset: d => d.pixelOffset,
                textAnchor: 'middle',
                alignmentBaseline: 'top',
                pickable: false,
                parameters: { depthTest: false }
            }),

            // Y axis title (VERTICAL)
            yTitleData.length > 0 && new TextLayer({
                id: `${this.props.id || 'axes'}-ytitle`,
                data: yTitleData,
                coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
                getPosition: d => d.position,
                getText: d => d.text,
                getSize: 12,
                getColor: labelColor!,
                sizeUnits: 'pixels',
                getPixelOffset: d => d.pixelOffset,
                textAnchor: 'middle',
                alignmentBaseline: 'center',
                getAngle: () => 90,     // rotate by 90 degrees
                pickable: false,
                parameters: { depthTest: false }
            }),
        ].filter(Boolean) as any[];
    }
}
