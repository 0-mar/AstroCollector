import {useForm} from "react-hook-form";
import {zoomFormSchema, type ZoomValues} from "@/features/search/photometricDataSection/schema.ts";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage} from "@/../components/ui/form.tsx";
import {Input} from "@/../components/ui/input.tsx";
import {Button} from "@/../components/ui/button.tsx";
import {useContext} from "react";
import {zodResolver} from "@hookform/resolvers/zod";
import {OptionsContext} from "@/features/search/photometricDataSection/components/plotOptions/OptionsContext.tsx";


const ZoomForm = () => {
    const optionsContext = useContext(OptionsContext)
    const form = useForm<ZoomValues>({
        resolver: zodResolver(zoomFormSchema),
        defaultValues: {
            xMin: 0,
            xMax: 0,
            yMin: 0,
            yMax: 0
        }
    });

    const onSubmit = (formData: ZoomValues) => {
        optionsContext?.setZoomToCoords({
            xMin: formData.xMin,
            xMax: formData.xMax,
            yMin: formData.yMin,
            yMax: formData.yMax
        })
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <h3 className="text-lg text-gray-900">Set plot viewport</h3>
                <FormField
                    control={form.control}
                    name="xMin"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Lower bound X</FormLabel>
                            <FormControl>
                                <Input className={"w-5/6"} {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="xMax"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Upper bound X</FormLabel>
                            <FormControl>
                                <Input className={"w-5/6"} {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="yMin"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Lower bound Y</FormLabel>
                            <FormControl>
                                <Input className={"w-5/6"} {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="yMax"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Upper bound Y</FormLabel>
                            <FormControl>
                                <Input className={"w-5/6"} {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                {<p className="text-destructive text-sm">{form.formState.errors.global?.message}</p>}
                <Button type={"submit"}>Zoom</Button>
            </form>
        </Form>
    )
}

export default ZoomForm;
