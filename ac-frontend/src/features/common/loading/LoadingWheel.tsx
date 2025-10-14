type LoadingWheelProps = {
    width: string,
    height: string
}

const LoadingWheel = ({width, height}: LoadingWheelProps) => {
    return (
        <div className="spinner" style={{width: `${width}`, height: `${height}`}}/>
    )
}

export default LoadingWheel
