import { cloneElement } from 'react'
import HelpPanel from '@/components/template/HelpPanel'
import type { ReactNode } from 'react'
import type { CommonProps } from '@/@types/common'

interface SplitProps extends CommonProps {
    content?: ReactNode
}

const Split = ({ children, content, ...rest }: SplitProps) => {
    return (
        <div className="relative grid h-full bg-white p-6 dark:bg-gray-800 lg:grid-cols-2">
            <div className="absolute right-6 top-6 z-10 flex items-center gap-2">
                <span className="hidden text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-300 md:inline">
                    Need help?
                </span>
                <HelpPanel
                    hoverable={false}
                    className="text-xl text-gray-500 hover:text-primary-500 dark:text-gray-200"
                />
            </div>
            <div className="hidden flex-col items-center justify-center rounded-3xl bg-primary bg-cover bg-no-repeat py-6 px-16 lg:flex">
                <div className="flex flex-col items-center gap-12">
                    <img
                        className="max-w-[450px] 2xl:max-w-[900px]"
                        src="/img/others/auth-split-img.png"
                    />
                    <div className="max-w-[550px] text-center">
                        <h1 className="text-neutral">
                            The easiest way to build your admin app
                        </h1>
                        <p className="mx-auto mt-8 font-semibold text-neutral opacity-80">
                            Experience seamless project management with Ecme.
                            Simplify your workflow, and achieve your goals
                            efficiently with our powerful and intuitive tools.
                        </p>
                    </div>
                </div>
            </div>
            <div className="flex flex-col items-center justify-center">
                <div className="w-full max-w-[380px] px-8 xl:max-w-[450px]">
                    <div className="mb-8">{content}</div>
                    {children
                        ? cloneElement(children as React.ReactElement, {
                              ...rest,
                          })
                        : null}
                </div>
            </div>
        </div>
    )
}

export default Split
