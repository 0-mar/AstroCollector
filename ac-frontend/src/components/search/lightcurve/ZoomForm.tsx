import {useForm} from "react-hook-form";
import {yupResolver} from "@hookform/resolvers/yup";
import {zoomFormSchema, type ZoomValues} from "@/features/search/lightcurve/schema.ts";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage} from "../../../../components/ui/form.tsx";
import {Input} from "../../../../components/ui/input.tsx";
import {Button} from "../../../../components/ui/button.tsx";
import {useContext, useEffect} from "react";
import {OptionsContext} from "@/components/search/lightcurve/OptionsContext.tsx";
import {RangeContext} from "@/components/search/lightcurve/CurrentRangeContext.tsx";


const LabeledInput = ({label, ...props}) => {
    return (
        <div className={"flex gap-x-2 items-center"}>
            <Input className={"w-5/6"} placeholder={"12235.55"} {...props} />
            <span className={"w-1/6"}>{label}</span>
        </div>
    )
}


const ZoomForm = () => {
    const context = useContext(OptionsContext)
    const rangeContext = useContext(RangeContext)
    const form = useForm<ZoomValues>({
        resolver: yupResolver(zoomFormSchema),
    });

    useEffect(() => {
        form.setValue("min", rangeContext?.currMinRange)
        form.setValue("max", rangeContext?.currMaxRange)
    }, [rangeContext?.currMinRange, rangeContext?.currMaxRange])

    const onSubmit = (formData: ZoomValues) => {
        if (formData.min !== null) {
            context?.setMinRange(formData.min)
        }
        if (formData.max !== null) {
            context?.setMaxRange(formData.max)
        }
        context?.setPlotVersion(context?.plotVersion + 1)
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <h3>Zoom to MJD</h3>
                <FormField
                    control={form.control}
                    name="min"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Lower bound</FormLabel>
                            <FormControl>
                                <LabeledInput label={"MJD"} {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="max"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Upper bound</FormLabel>
                            <FormControl>
                                <LabeledInput label={"MJD"} {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                {<p className="text-destructive text-sm">{form.formState.errors.global?.message}</p>}
                <Button type={"submit"}>Zoom</Button>
                <Button type={"button"} onClick={() => {
                    context?.setMinRange(undefined);
                    context?.setMaxRange(undefined)
                }}>Reset</Button>

            </form>
        </Form>
    )
}

export default ZoomForm;
